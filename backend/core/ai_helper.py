from difflib import SequenceMatcher
from json import loads as json_loads
from logging import Logger, getLogger
from pathlib import Path
from re import (
    IGNORECASE,
    Match,
    Pattern,
    compile as re_compile,
    findall as re_findall,
    match as re_match,
    search as re_search,
    split as re_split,
    sub as re_sub,
)
from typing import Any, Dict, List, Optional, Set, Tuple

from httpx import Client as HttpClient, Response as HttpResponse

from config import OLLAMA_HOST, OLLAMA_MODEL

logger: Logger = getLogger("anime_refresher.ai")


class AIHelper:
    """
    Intelligent title parser, fuzzy matcher, and Ollama LLM integration helper.

    Attributes
    ----------
    host : str
        Endpoint URL for the local Ollama LLM service.
    model : str
        Target Ollama model identifier.
    """

    host: str
    model: str
    _WIN_FORBIDDEN: Pattern[str] = re_compile(r'[<>:"/\\|?*\x00-\x1f]')
    _STOPWORDS: Set[str] = {
        "the",
        "a",
        "an",
        "of",
        "in",
        "to",
        "is",
        "for",
        "and",
        "with",
        "on",
        "at",
        "by",
        "from",
        "about",
    }
    _ROMAN_MAP: Dict[str, str] = {
        "x": "10",
        "ix": "9",
        "viii": "8",
        "vii": "7",
        "vi": "6",
        "v": "5",
        "iv": "4",
        "iii": "3",
        "ii": "2",
        "i": "1",
    }

    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL) -> None:
        """
        Initialize the AI helper for title normalization, scoring, and episode extraction.

        Parameters
        ----------
        host : str, default=OLLAMA_HOST
            Ollama API server host endpoint.
        model : str, default=OLLAMA_MODEL
            Ollama model identifier.
        """
        self.host: str = host.rstrip("/")
        self.model: str = model

    def parse_episode_numbers(self, filenames: List[str]) -> Set[int]:
        """
        Extract unique episode integers from a list of filenames using regex with Ollama fallback.

        Parameters
        ----------
        filenames : List[str]
            List of video file names to parse.

        Returns
        -------
        Set[int]
            Set of extracted integer episode sequence numbers.
        """
        if not filenames:
            return set()

        # Fast deterministic regex parsing
        episodes_regex: Set[int] = self._regex_extract_episodes(filenames)
        if len(episodes_regex) == len(filenames) or (
            len(episodes_regex) > 0 and len(filenames) <= len(episodes_regex) + 2
        ):
            logger.debug(
                f"Regex extracted {len(episodes_regex)} episodes: {sorted(episodes_regex)}"
            )
            return episodes_regex

        # If regex could not resolve all files, consult Ollama
        logger.debug(
            f"Ambiguous filenames detected ({len(episodes_regex)}/{len(filenames)} parsed). "
            "Consulting Ollama..."
        )
        episodes_ai: Optional[Set[int]] = self._ollama_extract_episodes(filenames)
        if episodes_ai:
            logger.debug(f"Ollama extracted episodes: {episodes_ai}")
            return episodes_ai

        return episodes_regex

    def _ollama_extract_episodes(self, filenames: List[str]) -> Optional[Set[int]]:
        """
        Query local AI/Ollama to parse episode numbers from filenames if available.

        Parameters
        ----------
        filenames : List[str]
            List of video filenames to send for extraction.

        Returns
        -------
        Optional[Set[int]]
            Parsed set of episode numbers, or None if request fails.
        """
        prompt: str = (
            "You are a file parser. Given these video filenames, extract all distinct episode numbers "
            "as a JSON array of integers.\n"
            "Return ONLY a JSON array, for example: [1, 2, 3, 4]. No explanations.\n\n"
            "Filenames:\n" + "\n".join(filenames[:50])
        )
        try:
            with HttpClient(timeout=1.0) as client:
                response: HttpResponse = client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                if response.status_code == 200:
                    data: Dict[str, Any] = response.json()
                    raw_response: str = data.get("response", "").strip()
                    parsed: Any = json_loads(raw_response)
                    if isinstance(parsed, list):
                        return {
                            int(item)
                            for item in parsed
                            if isinstance(item, (int, float, str)) and str(item).isdigit()
                        }
                    elif isinstance(parsed, dict):
                        for candidate_value in parsed.values():
                            if isinstance(candidate_value, list):
                                return {
                                    int(item)
                                    for item in candidate_value
                                    if str(item).isdigit()
                                }
        except Exception as error:
            logger.debug(f"AI episode extraction unavailable or timed out: {error}")
        return None

    def _regex_extract_episodes(self, filenames: List[str]) -> Set[int]:
        """
        Deterministic regex parsing for anime episode numbers.

        Parameters
        ----------
        filenames : List[str]
            List of video filenames to extract numbers from.

        Returns
        -------
        Set[int]
            Set of extracted integer episode numbers.
        """
        episodes: Set[int] = set()
        for name in filenames:
            stem: str = Path(name).stem

            # 1. Hyphen delimiter: ' - 01' (greedy search for last hyphen delimiter)
            regex_match: Optional[Match[str]] = re_search(
                r"\s+-\s+(\d{1,4})(?:v\d)?(?:\s*\[|\s*\(|\s*$)", stem
            )
            if regex_match:
                episodes.add(int(regex_match.group(1)))
                continue

            # 2. Episode / EP / E prefix: 'Episode 01', 'EP 01', 'E01'
            regex_match: Optional[Match[str]] = re_search(
                r"(?:\bEpisode\s*|\bEP\s*|\bE)(\d{1,4})(?:v\d)?(?:\s*\[|\s*\(|\s*$)",
                stem,
                IGNORECASE,
            )
            if regex_match:
                episodes.add(int(regex_match.group(1)))
                continue

            # 3. S01E05 or 1x05
            regex_match: Optional[Match[str]] = re_search(
                r"(?:S\d+E|(?:\b\d+)x)(\d{1,4})", stem, IGNORECASE
            )
            if regex_match:
                episodes.add(int(regex_match.group(1)))
                continue

            # 4. Trailing integer at the end of the stem (ignoring trailing tags)
            clean_stem: str = re_sub(r"\[.*?\]|\(.*?\)", "", stem).strip()
            regex_match: Optional[Match[str]] = re_search(
                r"(?:^|[\s_.])(\d{1,4})(?:v\d)?$", clean_stem
            )
            if regex_match:
                episodes.add(int(regex_match.group(1)))
                continue

            # 5. Last standalone integer in clean string
            matches: List[str] = re_findall(r"\b(\d{1,4})\b", clean_stem)
            if matches:
                episodes.add(int(matches[-1]))

        return episodes

    def format_folder_indexed_filename(
        self,
        anime_folder_name: str,
        episode_num: int,
        downloaded_ext: str = ".mp4",
        existing_filenames: Optional[List[str]] = None,
    ) -> str:
        """
        Format filename strictly using the template: '<Anime folder name> <index>.<format>'

        Determines digit padding (01 vs 001) from existing files or defaults to 2 digits.

        Parameters
        ----------
        anime_folder_name : str
            Base folder name of the series.
        episode_num : int
            Episode sequence number.
        downloaded_ext : str, default=".mp4"
            File extension.
        existing_filenames : Optional[List[str]], default=None
            Existing filenames in the folder to determine padding.

        Returns
        -------
        str
            Formatted filename.
        """
        digits: int = 2
        if existing_filenames:
            for file_name in existing_filenames:
                regex_match: Optional[Match[str]] = re_search(
                    r"(?:^|[\s_.-])(\d{2,4})(?:v\d)?(?:\.[\w\d]+)?$",
                    Path(file_name).stem,
                )
                if regex_match:
                    digits: int = max(digits, len(regex_match.group(1)))
                    break

        formatted_episode: str = f"{episode_num:0{digits}d}"
        return f"{anime_folder_name} {formatted_episode}{downloaded_ext}"

    def _ollama_format_name(
        self,
        existing_filenames: List[str],
        episode_num: int,
        downloaded_ext: str = ".mp4",
    ) -> Optional[str]:
        """
        Query Ollama to extrapolate the sequential filename from existing files.

        Parameters
        ----------
        existing_filenames : List[str]
            List of existing filenames in the series directory.
        episode_num : int
            Episode sequence number to format.
        downloaded_ext : str, default=".mp4"
            File extension for the target media file.

        Returns
        -------
        Optional[str]
            AI-suggested filename string or None if unavailable.
        """
        prompt: str = (
            "Given these existing anime episode filenames:\n"
            + "\n".join(existing_filenames[:10])
            + f"\n\nFormat the sequential filename for episode {episode_num} matching this pattern exactly.\n"
            f'Return ONLY a JSON object: {{"filename": "..."}}'
        )
        try:
            with HttpClient(timeout=1.5) as client:
                response: HttpResponse = client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                if response.status_code == 200:
                    response_data: Dict[str, Any] = response.json()
                    raw_response: str = response_data.get("response", "").strip()
                    parsed: Any = json_loads(raw_response)
                    if isinstance(parsed, dict) and "filename" in parsed:
                        return str(parsed["filename"])
        except Exception as error:
            logger.debug(f"AI filename formatting unavailable: {error}")
        return None

    def format_sequential_filename(
        self,
        anime_folder_name: str,
        existing_filenames: List[str],
        episode_num: int,
        downloaded_ext: str = ".mp4",
    ) -> str:
        """
        Generate a sequential filename matching the existing naming pattern in the folder.

        Parameters
        ----------
        anime_folder_name : str
            Series directory name.
        existing_filenames : List[str]
            List of already existing video files in the series directory.
        episode_num : int
            Episode sequence number to name.
        downloaded_ext : str, default=".mp4"
            Target extension for the file.

        Returns
        -------
        str
            Synthesized filename matching existing convention.
        """
        if existing_filenames:
            # 1. Primary: Fast deterministic pattern matching against existing files
            sample: str = existing_filenames[0]
            extension: str = downloaded_ext if downloaded_ext else Path(sample).suffix
            stem: str = Path(sample).stem

            # Match Season/Episode format (e.g. S01E05, S1E05, 1x05)
            match_season: Optional[Match[str]] = re_search(
                r"^(.*?)(S(\d+)E|(?:\b(\d+))x)(\d{1,4})(.*)$", stem, IGNORECASE
            )
            if match_season:
                prefix: str = match_season.group(1)
                season_prefix: str = match_season.group(2)
                sample_digits: int = len(match_season.group(5))
                suffix_extra: str = match_season.group(6).rstrip()
                formatted_episode: str = f"{episode_num:0{max(sample_digits, 2)}d}"
                season_match: Optional[Match[str]] = re_match(
                    r"^(S\d+E|(?:\d+)x)", season_prefix, IGNORECASE
                )
                if season_match:
                    return f"{prefix}{season_match.group(1)}{formatted_episode}{suffix_extra}{extension}"

            # Match Episode / EP / E explicit tag (e.g. "Show - Episode 01", "Show EP01")
            match_episode_tag: Optional[Match[str]] = re_search(
                r"^(.*?)(?:\s+-\s+|\s+)(Episode|EP|E)\s*(\d{1,4})(.*)$", stem, IGNORECASE
            )
            if match_episode_tag:
                prefix: str = match_episode_tag.group(1).strip()
                tag: str = match_episode_tag.group(2)
                sample_digits: int = len(match_episode_tag.group(3))
                suffix_extra: str = match_episode_tag.group(4).rstrip()
                formatted_episode: str = f"{episode_num:0{max(sample_digits, 2)}d}"
                separator: str = " - " if " - " in stem else " "
                return f"{prefix}{separator}{tag} {formatted_episode}{suffix_extra}{extension}"

            # Match standard hyphen pattern: "{prefix} - {ep}{suffix}"
            match_hyphen: Optional[Match[str]] = re_search(r"^(.*?)\s*-\s*(\d{1,4})(.*)$", stem)
            if match_hyphen:
                prefix: str = match_hyphen.group(1).strip()
                sample_digits: int = len(match_hyphen.group(2))
                suffix_extra: str = match_hyphen.group(3).rstrip()
                formatted_episode: str = f"{episode_num:0{max(sample_digits, 2)}d}"
                return f"{prefix} - {formatted_episode}{suffix_extra}{extension}"

            # Match spaced pattern without hyphen: "{prefix} {ep}{suffix}"
            match_space: Optional[Match[str]] = re_search(r"^(.*?)\s+(\d{1,4})(.*)$", stem)
            if match_space:
                prefix: str = match_space.group(1).strip()
                sample_digits: int = len(match_space.group(2))
                suffix_extra: str = match_space.group(3).rstrip()
                formatted_episode: str = f"{episode_num:0{max(sample_digits, 2)}d}"
                return f"{prefix} {formatted_episode}{suffix_extra}{extension}"

            # 2. Secondary: Fallback to AI helper if available
            suggested: Optional[str] = self._ollama_format_name(
                existing_filenames, episode_num, downloaded_ext
            )
            if suggested:
                if downloaded_ext:
                    suggested: str = Path(suggested).with_suffix(downloaded_ext).name
                return suggested

        # Default standard format
        return f"{anime_folder_name} - {episode_num:02d}{downloaded_ext}"

    def decompose_search_queries(self, folder_title: str) -> List[str]:
        """
        Generate progressive fallback search queries for Animepahe.

        1. Full cleaned title.
        2. Base franchise title (stripped of Roman numerals, Season X, Part X, Act X).
        3. Significant sub-clause splitting (colons, dashes, 'I am / I'm').
        4. Distinctive 2-word and 3-word token tuples.

        Parameters
        ----------
        folder_title : str
            Raw anime folder title.

        Returns
        -------
        List[str]
            Progressive fallback query strings.
        """
        queries: List[str] = []
        clean_title: str = self._WIN_FORBIDDEN.sub(" ", folder_title).strip()
        clean_title: str = re_sub(r"\s+", " ", clean_title)
        if clean_title:
            queries.append(clean_title)

        # Base franchise title: strip trailing season tags, Roman numerals, and subtitle parts
        base_title: str = re_sub(
            r"\s+(?:season\s+\d+|s\d+|\d+(?:st|nd|rd|th)\s+season|part\s+\d+|act\.\d+|cour\s+\d+)\b",
            "",
            clean_title,
            flags=IGNORECASE,
        )
        base_title: str = re_sub(
            r"\s+(?:x|ix|viii|vii|vi|v|iv|iii|ii|i)\b\s*$", "", base_title, flags=IGNORECASE
        )
        base_title: str = re_sub(r"[:\-–—]\s*.*$", "", base_title).strip()
        base_title: str = re_sub(r"\s+", " ", base_title)

        if base_title and base_title.lower() not in [q.lower() for q in queries]:
            queries.append(base_title)

        # Sub-clauses after colon/dash or 'I am / I'm'
        parts: List[str] = re_split(
            r"[:\-–—]\s*|\s+(?:I\'m|I am)\s+", clean_title, flags=IGNORECASE
        )
        for part in parts:
            part_cleaned: str = part.strip()
            if len(part_cleaned) > 4 and part_cleaned.lower() not in [
                q.lower() for q in queries
            ]:
                queries.append(part_cleaned)

        # Distinctive key phrase pruning: extract top 2-word and 3-word distinctive tokens
        tokens: List[str] = [
            word
            for word in re_split(r"[\s_\-]+", clean_title)
            if word.lower() not in self._STOPWORDS and len(word) > 1
        ]
        if len(tokens) >= 2:
            query_two: str = " ".join(tokens[:2])
            if query_two.lower() not in [q.lower() for q in queries]:
                queries.append(query_two)
            if len(tokens) >= 3:
                query_three: str = " ".join(tokens[:3])
                if query_three.lower() not in [q.lower() for q in queries]:
                    queries.append(query_three)

        return queries

    def calculate_title_similarity(self, folder_title: str, candidate_title: str) -> float:
        """
        Calculate a confidence similarity score (0.0 to 1.0) between a folder title and candidate.

        Accounts for Windows symbol stripping, Roman numerals, and season normalization.

        Parameters
        ----------
        folder_title : str
            Local series folder title.
        candidate_title : str
            Candidate anime title returned by provider.

        Returns
        -------
        float
            Similarity score between 0.0 and 1.0.
        """
        if not folder_title or not candidate_title:
            return 0.0

        def normalize_string(raw_string: str) -> str:
            """
            Normalize anime title strings for uniform comparison.

            Parameters
            ----------
            raw_string : str
                Raw anime title string.

            Returns
            -------
            str
                Sanitized string with unified roman numerals, symbols, and season tags.
            """
            cleaned: str = self._WIN_FORBIDDEN.sub(" ", raw_string).lower()
            cleaned: str = re_sub(r"[^\w\s]", " ", cleaned)
            for roman_numeral, arabic_numeral in self._ROMAN_MAP.items():
                cleaned: str = re_sub(rf"\b{roman_numeral}\b", arabic_numeral, cleaned)
            cleaned: str = re_sub(r"\bs(\d+)\b", r"season \1", cleaned)
            cleaned: str = re_sub(r"(\d+)(?:st|nd|rd|th)\s+season", r"season \1", cleaned)
            return re_sub(r"\s+", " ", cleaned).strip()

        norm_folder: str = normalize_string(folder_title)
        norm_candidate: str = normalize_string(candidate_title)

        # Exact normalized match
        if norm_folder == norm_candidate:
            return 1.0

        # One is full prefix or subset of other
        if norm_folder in norm_candidate or norm_candidate in norm_folder:
            ratio: float = min(len(norm_folder), len(norm_candidate)) / max(
                len(norm_folder), len(norm_candidate)
            )
            if ratio >= 0.7:
                return 0.95
            return 0.85

        # Token Jaccard & overlap
        folder_tokens: Set[str] = set(norm_folder.split())
        candidate_tokens: Set[str] = set(norm_candidate.split())
        if not folder_tokens or not candidate_tokens:
            return 0.0

        intersection: Set[str] = folder_tokens.intersection(candidate_tokens)
        union: Set[str] = folder_tokens.union(candidate_tokens)
        jaccard: float = len(intersection) / len(union)

        # Check if all folder tokens are in candidate
        if folder_tokens.issubset(candidate_tokens):
            return 0.90 + 0.08 * (len(folder_tokens) / len(candidate_tokens))

        # Check sequence matcher ratio
        sequence_ratio: float = SequenceMatcher(None, norm_folder, norm_candidate).ratio()

        # Weighted combination of sequence matcher and token overlap
        combined: float = 0.6 * sequence_ratio + 0.4 * jaccard
        return round(combined, 3)

    def rank_and_score_candidates(
        self,
        folder_title: str,
        candidates: List[Dict[str, Any]],
        threshold: float = 0.75,
    ) -> Tuple[Optional[Dict[str, Any]], float, Optional[Dict[str, Any]], float]:
        """
        Evaluate and score all candidates from Animepahe search results.

        Parameters
        ----------
        folder_title : str
            Local series folder title.
        candidates : List[Dict[str, Any]]
            Search result candidate dictionaries.
        threshold : float, default=0.75
            Minimum similarity score required to accept match.

        Returns
        -------
        Tuple[Optional[Dict[str, Any]], float, Optional[Dict[str, Any]], float]
            (best_matched_candidate, best_score, closest_candidate, closest_score)
        """
        if not candidates:
            return None, 0.0, None, 0.0

        scored_candidates: List[Tuple[Dict[str, Any], float]] = []
        for candidate in candidates:
            candidate_title: str = candidate.get("title", "")
            if not candidate_title:
                continue
            score: float = self.calculate_title_similarity(folder_title, candidate_title)
            scored_candidates.append((candidate, score))

        if not scored_candidates:
            return None, 0.0, None, 0.0

        scored_candidates.sort(key=lambda item: item[1], reverse=True)
        closest_candidate: Dict[str, Any]
        closest_score: float
        closest_candidate, closest_score = scored_candidates[0]

        if closest_score >= threshold:
            logger.debug(
                f"Candidate match found for '{folder_title}': '{closest_candidate.get('title')}' "
                f"(Score: {closest_score})"
            )
            return closest_candidate, closest_score, closest_candidate, closest_score

        logger.debug(
            f"Closest candidate for '{folder_title}' was '{closest_candidate.get('title')}' "
            f"(Score: {closest_score} < threshold {threshold})"
        )
        return None, 0.0, closest_candidate, closest_score

    def is_title_match(self, folder_title: str, candidate_title: str) -> bool:
        """
        Determine whether a local anime folder title and candidate match the same series and season.

        Parameters
        ----------
        folder_title : str
            Local anime folder title.
        candidate_title : str
            Provider search candidate title.

        Returns
        -------
        bool
            True if determined to refer to the identical series/season, False otherwise.
        """
        if not folder_title or not candidate_title:
            return False

        def base_norm(raw_string: str) -> str:
            """
            Normalize whitespace and non-word characters for exact baseline comparison.

            Parameters
            ----------
            raw_string : str
                Raw anime title string.

            Returns
            -------
            str
                Lowercase string with stripped punctuation and normalized whitespace.
            """
            return re_sub(
                r"\s+", " ", re_sub(r"[^\w\s]", " ", raw_string)
            ).strip().lower()

        def win_strip(raw_string: str) -> str:
            """
            Normalize string by stripping Windows-forbidden filesystem characters.

            Parameters
            ----------
            raw_string : str
                Raw anime title string.

            Returns
            -------
            str
                Sanitized lowercase string without Windows filesystem forbidden characters.
            """
            return re_sub(
                r"\s+", " ", self._WIN_FORBIDDEN.sub(" ", raw_string)
            ).strip().lower()

        # Fast Path 1: Full normalized exact match
        norm_folder: str = base_norm(folder_title)
        norm_candidate: str = base_norm(candidate_title)

        if norm_folder == norm_candidate:
            logger.debug(f"[Fast Match] '{folder_title}' == '{candidate_title}'")
            return True

        # Fast Path 2: Season shorthand normalization
        def season_norm(norm_string: str) -> str:
            """
            Normalize season shorthand indicators to explicit full form.

            Parameters
            ----------
            norm_string : str
                Pre-normalized anime title string.

            Returns
            -------
            str
                String with unified season tokens.
            """
            normalized_season: str = re_sub(r"\bs(\d+)\b", r"season \1", norm_string)
            normalized_season: str = re_sub(
                r"(\d+)(?:st|nd|rd|th)\s+season", r"season \1", normalized_season
            )
            return normalized_season

        if season_norm(norm_folder) == season_norm(norm_candidate):
            logger.debug(f"[Fast Season Match] '{folder_title}' == '{candidate_title}'")
            return True

        # Fast Path 3: Windows symbol-aware comparison
        win_folder: str = win_strip(folder_title)
        win_candidate: str = win_strip(candidate_title)

        if win_folder == win_candidate:
            logger.debug(
                f"[Win-Strip Match] '{folder_title}' ~= '{candidate_title}' "
                "(symbol gap explained by Windows FS)"
            )
            return True

        if season_norm(win_folder) == season_norm(win_candidate):
            logger.debug(f"[Win-Strip Season Match] '{folder_title}' ~= '{candidate_title}'")
            return True

        # Fast Path 4: Token subset check
        folder_tokens: Set[str] = set(norm_folder.split())
        candidate_tokens: Set[str] = set(norm_candidate.split())
        if folder_tokens and folder_tokens.issubset(candidate_tokens):
            if len(candidate_tokens) <= len(folder_tokens) + 4:
                logger.debug(f"[Token Subset Match] '{folder_title}' tokens ⊆ '{candidate_title}'")
                return True

        # AI Path: Semantic deduction with explicit Windows context
        logger.debug(
            f"Titles differ. Consulting AI for match: '{folder_title}' vs '{candidate_title}'..."
        )
        prompt: str = (
            f"You are an anime title comparator.\n"
            f'Folder Title (local): "{folder_title}"\n'
            f'Search Result Title: "{candidate_title}"\n\n'
            f"IMPORTANT CONTEXT: Windows does not allow the following characters in folder names: "
            f': * ? " < > | / \\ — so users are forced to drop or replace these symbols when '
            f"creating the folder. This means the folder title may be a symbol-stripped version "
            f"of the real anime title. For example:\n"
            f'  Real title: "Mecha-Ude: Mechanical Arms" -> Folder: "Mecha-Ude Mechanical Arms"\n'
            f"  Real title: \"Watari-kun's ****** Is About to Collapse\" -> Folder: \"Watari-kun's  Is About to Collapse\"\n\n"
            f"Do these two titles refer to the exact same anime series and season? "
            f"Consider: alternative English/Japanese titles, Roman numerals, season abbreviations "
            f"(e.g. 'S3' = 'Season 3'), and Windows symbol-stripping. "
            f"Do NOT reject a match solely because the folder name is missing colons, asterisks, "
            f"slashes, or other symbols that Windows forbids.\n"
            f'Return ONLY a JSON object: {{"match": true}} or {{"match": false}}.'
        )

        try:
            with HttpClient(timeout=2.5) as client:
                response: HttpResponse = client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                if response.status_code == 200:
                    response_data: Dict[str, Any] = response.json()
                    raw_response: str = response_data.get("response", "").strip()
                    parsed_result: Any = json_loads(raw_response)
                    if isinstance(parsed_result, dict) and "match" in parsed_result:
                        is_matched: bool = bool(parsed_result["match"])
                        logger.debug(
                            f"AI match decision for '{folder_title}' vs '{candidate_title}': {is_matched}"
                        )
                        return is_matched
        except Exception as error:
            logger.debug(f"AI title matching unavailable or timed out: {error}")

        return False
