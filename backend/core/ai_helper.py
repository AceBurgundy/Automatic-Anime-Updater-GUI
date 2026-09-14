import json
import logging
import re
from pathlib import Path
from typing import List, Set, Optional
import httpx
from config import OLLAMA_HOST, OLLAMA_MODEL

logger = logging.getLogger("anime_refresher.ai")

class AIHelper:
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host.rstrip("/")
        self.model = model

    def parse_episode_numbers(self, filenames: List[str]) -> Set[int]:
        """Extracts unique episode integers from a list of filenames using regex with Ollama fallback."""
        if not filenames:
            return set()

        # Fast deterministic regex parsing
        episodes_regex = self._regex_extract_episodes(filenames)
        if len(episodes_regex) == len(filenames) or (len(episodes_regex) > 0 and len(filenames) <= len(episodes_regex) + 2):
            logger.debug(f"Regex extracted {len(episodes_regex)} episodes: {sorted(episodes_regex)}")
            return episodes_regex

        # If regex couldn't resolve all files, consult Ollama
        logger.debug(f"Ambiguous filenames detected ({len(episodes_regex)}/{len(filenames)} parsed). Consulting Ollama...")
        episodes_ai = self._ollama_extract_episodes(filenames)
        if episodes_ai:
            logger.debug(f"Ollama extracted episodes: {episodes_ai}")
            return episodes_ai

        return episodes_regex

    def _ollama_extract_episodes(self, filenames: List[str]) -> Optional[Set[int]]:
        """Queries local AI/Ollama to parse episode numbers from filenames if available."""
        prompt = (
            "You are a file parser. Given these video filenames, extract all distinct episode numbers as a JSON array of integers.\n"
            "Return ONLY a JSON array, for example: [1, 2, 3, 4]. No explanations.\n\n"
            "Filenames:\n" + "\n".join(filenames[:50])
        )
        try:
            with httpx.Client(timeout=1.0) as client:
                res = client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    raw_response = data.get("response", "").strip()
                    parsed = json.loads(raw_response)
                    if isinstance(parsed, list):
                        return {int(x) for x in parsed if isinstance(x, (int, float, str)) and str(x).isdigit()}
                    elif isinstance(parsed, dict):
                        for val in parsed.values():
                            if isinstance(val, list):
                                return {int(x) for x in val if str(x).isdigit()}
        except Exception as e:
            logger.debug(f"AI episode extraction unavailable or timed out: {e}")
        return None

    def _regex_extract_episodes(self, filenames: List[str]) -> Set[int]:
        """Deterministic regex parsing for anime episode numbers."""
        episodes = set()
        for name in filenames:
            stem = Path(name).stem

            # 1. Hyphen delimiter: ' - 01' (greedy search for last hyphen delimiter)
            m = re.search(r'\s+-\s+(\d{1,4})(?:v\d)?(?:\s*\[|\s*\(|\s*$)', stem)
            if m:
                episodes.add(int(m.group(1)))
                continue

            # 2. Episode / EP / E prefix: 'Episode 01', 'EP 01', 'E01'
            m = re.search(r'(?:\bEpisode\s*|\bEP\s*|\bE)(\d{1,4})(?:v\d)?(?:\s*\[|\s*\(|\s*$)', stem, re.IGNORECASE)
            if m:
                episodes.add(int(m.group(1)))
                continue

            # 3. S01E05 or 1x05
            m = re.search(r'(?:S\d+E|(?:\b\d+)x)(\d{1,4})', stem, re.IGNORECASE)
            if m:
                episodes.add(int(m.group(1)))
                continue

            # 4. Trailing integer at the end of the stem (ignoring trailing tags like [1080p], (1080p), [HASH])
            clean = re.sub(r'\[.*?\]|\(.*?\)', '', stem).strip()
            m = re.search(r'(?:^|[\s_.])(\d{1,4})(?:v\d)?$', clean)
            if m:
                episodes.add(int(m.group(1)))
                continue

            # 5. Last standalone integer in clean string
            matches = re.findall(r'\b(\d{1,4})\b', clean)
            if matches:
                episodes.add(int(matches[-1]))

        return episodes

    def format_folder_indexed_filename(
        self,
        anime_folder_name: str,
        episode_num: int,
        downloaded_ext: str = ".mp4",
        existing_filenames: Optional[List[str]] = None
    ) -> str:
        """
        Formats filename strictly using the template: '<Anime folder name> <index>.<format>'
        Determines digit padding (01 vs 001) from existing files or defaults to 2 digits.
        """
        digits = 2
        if existing_filenames:
            for fname in existing_filenames:
                m = re.search(r'(?:^|[\s_.-])(\d{2,4})(?:v\d)?(?:\.[\w\d]+)?$', Path(fname).stem)
                if m:
                    digits = max(digits, len(m.group(1)))
                    break

        formatted_ep = f"{episode_num:0{digits}d}"
        return f"{anime_folder_name} {formatted_ep}{downloaded_ext}"

    def format_sequential_filename(
        self,
        anime_folder_name: str,
        existing_filenames: List[str],
        episode_num: int,
        downloaded_ext: str = ".mp4"
    ) -> str:
        """Generates a sequential filename matching the existing naming pattern in the folder."""
        if existing_filenames:
            # 1. Primary: Fast deterministic pattern matching against existing files
            sample = existing_filenames[0]
            ext = downloaded_ext if downloaded_ext else Path(sample).suffix
            stem = Path(sample).stem

            # Match Season/Episode format (e.g. S01E05, S1E05, 1x05)
            m_season = re.search(r'^(.*?)(S(\d+)E|(?:\b(\d+))x)(\d{1,4})(.*)$', stem, re.IGNORECASE)
            if m_season:
                prefix = m_season.group(1)
                season_prefix = m_season.group(2)
                sample_digits = len(m_season.group(5))
                suffix_extra = m_season.group(6).rstrip()
                formatted_ep = f"{episode_num:0{max(sample_digits, 2)}d}"
                # If season prefix was S01E, rebuild with same season
                s_match = re.match(r'^(S\d+E|(?:\d+)x)', season_prefix, re.IGNORECASE)
                if s_match:
                    return f"{prefix}{s_match.group(1)}{formatted_ep}{suffix_extra}{ext}"

            # Match Episode / EP / E explicit tag (e.g. "Show - Episode 01", "Show EP01")
            m_ep_tag = re.search(r'^(.*?)(?:\s+-\s+|\s+)(Episode|EP|E)\s*(\d{1,4})(.*)$', stem, re.IGNORECASE)
            if m_ep_tag:
                prefix = m_ep_tag.group(1).strip()
                tag = m_ep_tag.group(2)
                sample_digits = len(m_ep_tag.group(3))
                suffix_extra = m_ep_tag.group(4).rstrip()
                formatted_ep = f"{episode_num:0{max(sample_digits, 2)}d}"
                sep = " - " if " - " in stem else " "
                return f"{prefix}{sep}{tag} {formatted_ep}{suffix_extra}{ext}"

            # Match standard hyphen pattern: "{prefix} - {ep}{suffix}"
            m_hyphen = re.search(r'^(.*?)\s*-\s*(\d{1,4})(.*)$', stem)
            if m_hyphen:
                prefix = m_hyphen.group(1).strip()
                sample_digits = len(m_hyphen.group(2))
                suffix_extra = m_hyphen.group(3).rstrip()
                formatted_ep = f"{episode_num:0{max(sample_digits, 2)}d}"
                return f"{prefix} - {formatted_ep}{suffix_extra}{ext}"

            # Match spaced pattern without hyphen: "{prefix} {ep}{suffix}"
            m_space = re.search(r'^(.*?)\s+(\d{1,4})(.*)$', stem)
            if m_space:
                prefix = m_space.group(1).strip()
                sample_digits = len(m_space.group(2))
                suffix_extra = m_space.group(3).rstrip()
                formatted_ep = f"{episode_num:0{max(sample_digits, 2)}d}"
                return f"{prefix} {formatted_ep}{suffix_extra}{ext}"

            # 2. Secondary: Fallback to AI helper if available
            suggested = self._ollama_format_name(existing_filenames, episode_num, downloaded_ext)
            if suggested:
                if downloaded_ext:
                    suggested = Path(suggested).with_suffix(downloaded_ext).name
                return suggested

        # Default standard format
        return f"{anime_folder_name} - {episode_num:02d}{downloaded_ext}"

    # Characters Windows forbids in folder/file names — these will be missing from the folder title
    _WIN_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

    # Stopwords for keyword pruning in Tier 3 search
    _STOPWORDS = {"the", "a", "an", "of", "in", "to", "is", "for", "and", "with", "on", "at", "by", "from", "about"}

    # Roman numeral mapping
    _ROMAN_MAP = {
        "x": "10", "ix": "9", "viii": "8", "vii": "7", "vi": "6",
        "v": "5", "iv": "4", "iii": "3", "ii": "2", "i": "1"
    }

    def decompose_search_queries(self, folder_title: str) -> List[str]:
        """
        Generates progressive fallback search queries for Animepahe:
        1. Full cleaned title.
        2. Base franchise title (stripped of Roman numerals, Season X, Part X, Act X, arc suffixes).
        3. Significant sub-clause splitting (colons, dashes, 'I am / I'm').
        4. Distinctive 2-word and 3-word token tuples.
        """
        queries = []
        clean = self._WIN_FORBIDDEN.sub(' ', folder_title).strip()
        clean = re.sub(r'\s+', ' ', clean)
        if clean:
            queries.append(clean)

        # Base franchise title: strip trailing season tags, Roman numerals, and subtitle parts
        # e.g. "Is It Wrong to Try to Pick Up Girls in a Dungeon IV" -> "Is It Wrong to Try to Pick Up Girls in a Dungeon"
        base = re.sub(r'\s+(?:season\s+\d+|s\d+|\d+(?:st|nd|rd|th)\s+season|part\s+\d+|act\.\d+|cour\s+\d+)\b', '', clean, flags=re.IGNORECASE)
        base = re.sub(r'\s+(?:x|ix|viii|vii|vi|v|iv|iii|ii|i)\b\s*$', '', base, flags=re.IGNORECASE)
        base = re.sub(r'[:\-–—]\s*.*$', '', base).strip()
        base = re.sub(r'\s+', ' ', base)

        if base and base.lower() not in [q.lower() for q in queries]:
            queries.append(base)

        # Sub-clauses after colon/dash or 'I am / I'm'
        parts = re.split(r'[:\-–—]\s*|\s+(?:I\'m|I am)\s+', clean, flags=re.IGNORECASE)
        for p in parts:
            p = p.strip()
            if len(p) > 4 and p.lower() not in [q.lower() for q in queries]:
                queries.append(p)

        # Distinctive key phrase pruning: extract top 2-word and 3-word distinctive tokens
        tokens = [w for w in re.split(r'[\s_\-]+', clean) if w.lower() not in self._STOPWORDS and len(w) > 1]
        if len(tokens) >= 2:
            q2 = " ".join(tokens[:2])
            if q2.lower() not in [q.lower() for q in queries]:
                queries.append(q2)
            if len(tokens) >= 3:
                q3 = " ".join(tokens[:3])
                if q3.lower() not in [q.lower() for q in queries]:
                    queries.append(q3)

        return queries

    def calculate_title_similarity(self, folder_title: str, candidate_title: str) -> float:
        """
        Calculates a confidence similarity score (0.0 to 1.0) between a folder title and a candidate title.
        Accounts for Windows symbol stripping, Roman numerals, and season normalization.
        """
        if not folder_title or not candidate_title:
            return 0.0

        def _norm(s: str) -> str:
            s = self._WIN_FORBIDDEN.sub(' ', s).lower()
            s = re.sub(r'[^\w\s]', ' ', s)
            # Normalize Roman numerals to arabic numbers
            for r_num, arab in self._ROMAN_MAP.items():
                s = re.sub(rf'\b{r_num}\b', arab, s)
            s = re.sub(r'\bs(\d+)\b', r'season \1', s)
            s = re.sub(r'(\d+)(?:st|nd|rd|th)\s+season', r'season \1', s)
            return re.sub(r'\s+', ' ', s).strip()

        norm_f = _norm(folder_title)
        norm_c = _norm(candidate_title)

        # Exact normalized match
        if norm_f == norm_c:
            return 1.0

        # One is full prefix or subset of other
        if norm_f in norm_c or norm_c in norm_f:
            ratio = min(len(norm_f), len(norm_c)) / max(len(norm_f), len(norm_c))
            if ratio >= 0.7:
                return 0.95
            return 0.85

        # Token Jaccard & overlap
        f_tokens = set(norm_f.split())
        c_tokens = set(norm_c.split())
        if not f_tokens or not c_tokens:
            return 0.0

        intersection = f_tokens.intersection(c_tokens)
        union = f_tokens.union(c_tokens)
        jaccard = len(intersection) / len(union)

        # Check if all folder tokens are in candidate
        if f_tokens.issubset(c_tokens):
            return 0.90 + 0.08 * (len(f_tokens) / len(c_tokens))

        # Check sequence matcher ratio
        from difflib import SequenceMatcher
        seq_ratio = SequenceMatcher(None, norm_f, norm_c).ratio()

        # Weighted combination of sequence matcher and token overlap
        combined = 0.6 * seq_ratio + 0.4 * jaccard
        return round(combined, 3)

    def rank_and_score_candidates(
        self,
        folder_title: str,
        candidates: List[Dict[str, Any]],
        threshold: float = 0.75
    ) -> Tuple[Optional[Dict[str, Any]], float, Optional[Dict[str, Any]], float]:
        """
        Evaluates and scores all candidates from Animepahe search results.
        Returns: (best_matched_candidate, best_score, closest_candidate, closest_score)
        """
        if not candidates:
            return None, 0.0, None, 0.0

        scored_candidates = []
        for cand in candidates:
            cand_title = cand.get("title", "")
            if not cand_title:
                continue
            score = self.calculate_title_similarity(folder_title, cand_title)
            scored_candidates.append((cand, score))

        if not scored_candidates:
            return None, 0.0, None, 0.0

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        closest_cand, closest_score = scored_candidates[0]

        if closest_score >= threshold:
            logger.debug(f"Candidate match found for '{folder_title}': '{closest_cand.get('title')}' (Score: {closest_score})")
            return closest_cand, closest_score, closest_cand, closest_score

        logger.debug(f"Closest candidate for '{folder_title}' was '{closest_cand.get('title')}' (Score: {closest_score} < threshold {threshold})")
        return None, 0.0, closest_cand, closest_score


    def is_title_match(self, folder_title: str, candidate_title: str) -> bool:
        """
        Determines whether a local anime folder title and a search result candidate title
        refer to the exact same anime franchise and season.

        Handles Windows filesystem symbol-stripping: folder names cannot contain characters
        like : * ? " < > | / \\ so those are dropped or replaced by spaces when the user
        creates the folder. This means the folder name is a degraded version of the real title.

        Fast-path:
          1. Full normalized comparison (strip all symbols, collapse whitespace).
          2. Season shorthand normalization (s2 <-> Season 2, 2nd Season <-> Season 2).
          3. Windows symbol-aware subset check: strip Windows-forbidden chars from the
             candidate and compare against the folder name with the same treatment.
          4. Token subset check: every word in the folder name is present in the candidate.
        Falls back to AI deduction when all fast-paths miss.
        """
        if not folder_title or not candidate_title:
            return False

        def _base_norm(s: str) -> str:
            """Strip all punctuation/symbols, collapse whitespace, lowercase."""
            return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', s)).strip().lower()

        def _win_strip(s: str) -> str:
            """Remove Windows-forbidden characters, then collapse extra whitespace."""
            return re.sub(r'\s+', ' ', self._WIN_FORBIDDEN.sub(' ', s)).strip().lower()

        # --- Fast Path 1: Full normalized exact match ---
        norm_folder = _base_norm(folder_title)
        norm_cand = _base_norm(candidate_title)

        if norm_folder == norm_cand:
            logger.debug(f"[Fast Match] '{folder_title}' == '{candidate_title}'")
            return True

        # --- Fast Path 2: Season shorthand normalization ---
        def _season_norm(s: str) -> str:
            s = re.sub(r'\bs(\d+)\b', r'season \1', s)
            s = re.sub(r'(\d+)(?:st|nd|rd|th)\s+season', r'season \1', s)
            return s

        if _season_norm(norm_folder) == _season_norm(norm_cand):
            logger.debug(f"[Fast Season Match] '{folder_title}' == '{candidate_title}'")
            return True

        # --- Fast Path 3: Windows symbol-aware comparison ---
        # Strip Windows-forbidden chars from the candidate (simulating what Windows would produce)
        win_folder = _win_strip(folder_title)
        win_cand = _win_strip(candidate_title)

        if win_folder == win_cand:
            logger.debug(f"[Win-Strip Match] '{folder_title}' ~= '{candidate_title}' (symbol gap explained by Windows FS)")
            return True

        # Also apply season normalization after win-stripping
        if _season_norm(win_folder) == _season_norm(win_cand):
            logger.debug(f"[Win-Strip Season Match] '{folder_title}' ~= '{candidate_title}'")
            return True

        # --- Fast Path 4: Token subset check ---
        # All words in the folder name should be present in the candidate
        # (covers cases where the folder dropped symbols that separated words)
        folder_tokens = set(norm_folder.split())
        cand_tokens = set(norm_cand.split())
        if folder_tokens and folder_tokens.issubset(cand_tokens):
            # Only count as a match if the candidate isn't vastly longer (avoids false positives)
            if len(cand_tokens) <= len(folder_tokens) + 4:
                logger.debug(f"[Token Subset Match] '{folder_title}' tokens ⊆ '{candidate_title}'")
                return True

        # --- AI Path: Semantic deduction with explicit Windows context ---
        logger.debug(f"Titles differ. Consulting AI for match: '{folder_title}' vs '{candidate_title}'...")
        prompt = (
            f"You are an anime title comparator.\n"
            f"Folder Title (local): \"{folder_title}\"\n"
            f"Search Result Title: \"{candidate_title}\"\n\n"
            f"IMPORTANT CONTEXT: Windows does not allow the following characters in folder names: "
            f": * ? \" < > | / \\ — so users are forced to drop or replace these symbols when "
            f"creating the folder. This means the folder title may be a symbol-stripped version "
            f"of the real anime title. For example:\n"
            f"  Real title: \"Mecha-Ude: Mechanical Arms\" -> Folder: \"Mecha-Ude Mechanical Arms\"\n"
            f"  Real title: \"Watari-kun's ****** Is About to Collapse\" -> Folder: \"Watari-kun's  Is About to Collapse\"\n\n"
            f"Do these two titles refer to the exact same anime series and season? "
            f"Consider: alternative English/Japanese titles, Roman numerals, season abbreviations "
            f"(e.g. 'S3' = 'Season 3'), and Windows symbol-stripping. "
            f"Do NOT reject a match solely because the folder name is missing colons, asterisks, "
            f"slashes, or other symbols that Windows forbids.\n"
            f"Return ONLY a JSON object: {{\"match\": true}} or {{\"match\": false}}."
        )

        try:
            with httpx.Client(timeout=2.5) as client:
                res = client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    raw_response = data.get("response", "").strip()
                    parsed = json.loads(raw_response)
                    if isinstance(parsed, dict) and "match" in parsed:
                        is_matched = bool(parsed["match"])
                        logger.debug(f"AI match decision for '{folder_title}' vs '{candidate_title}': {is_matched}")
                        return is_matched
        except Exception as e:
            logger.debug(f"AI title matching unavailable or timed out: {e}")

        # Default to False if AI is unreachable or unsure to prevent downloading incorrect anime
        return False



