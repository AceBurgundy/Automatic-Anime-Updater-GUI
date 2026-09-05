import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus

from core.safety import safety_guard

logger = logging.getLogger("anime_refresher.reporter")

@dataclass
class AnimeErrorEntry:
    folder_name: str
    search_query: str
    closest_candidate: str
    similarity_score: float
    error_type: str
    human_message: str
    suggested_action: str
    animepahe_search_url: str
    timestamp: str

class ErrorReporter:
    """Manages collection of automation errors and renders an interactive modern errors.html report."""

    def __init__(self):
        self.errors: List[AnimeErrorEntry] = []

    def clear(self) -> None:
        """Clears all in-memory error records."""
        self.errors.clear()

    def has_errors(self) -> bool:
        """Checks if any errors have been recorded."""
        return len(self.errors) > 0

    def add_title_mismatch_error(
        self,
        folder_name: str,
        search_query: str,
        closest_candidate: str,
        similarity_score: float,
        base_url: str = "https://animepahe.pw"
    ) -> None:
        """Records a title mismatch or low-confidence search result error."""
        score_pct = int(similarity_score * 100)
        search_url = f"{base_url.rstrip('/')}/?q={quote_plus(folder_name)}"
        
        if closest_candidate:
            msg = (
                f"Search for '{folder_name}' returned '{closest_candidate}' as the closest result "
                f"(Match Confidence: {score_pct}%), which did not meet the required matching threshold."
            )
            suggestion = f"Please rename the folder to '{closest_candidate}' or check the official site title."
        else:
            msg = f"Search query '{search_query}' yielded 0 search results on Animepahe."
            suggestion = "Please check Animepahe to find the exact official Japanese or English title and rename the folder."

        entry = AnimeErrorEntry(
            folder_name=folder_name,
            search_query=search_query,
            closest_candidate=closest_candidate or "None found",
            similarity_score=round(similarity_score, 2),
            error_type="title_mismatch" if closest_candidate else "not_found",
            human_message=msg,
            suggested_action=suggestion,
            animepahe_search_url=search_url,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )
        self.errors.append(entry)

    def add_generic_error(
        self,
        folder_name: str,
        error_type: str,
        message: str,
        suggestion: str = "",
        base_url: str = "https://animepahe.pw"
    ) -> None:
        """Records a general download, network, or extraction failure."""
        search_url = f"{base_url.rstrip('/')}/?q={quote_plus(folder_name)}"
        entry = AnimeErrorEntry(
            folder_name=folder_name,
            search_query=folder_name,
            closest_candidate="N/A",
            similarity_score=0.0,
            error_type=error_type,
            human_message=message,
            suggested_action=suggestion or "Retry during the next automated cycle.",
            animepahe_search_url=search_url,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )
        self.errors.append(entry)

    def write_html_report(self, output_path: Path) -> bool:
        """Renders errors.html with an interactive dashboard and embedded JSON data."""
        try:
            safety_guard.verify_write_safety(output_path)
        except Exception as e:
            logger.error(f"Safety violation writing error report: {e}")
            return False

        # If no errors, remove existing error report or write empty clean state
        if not self.errors:
            if output_path.exists():
                try:
                    output_path.unlink()
                    logger.info("Removed previous errors.html (all series synchronized cleanly).")
                except Exception:
                    pass
            return True

        errors_json = json.dumps([asdict(e) for e in self.errors], ensure_ascii=False, indent=2)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anime Refresher - Attention Required</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --border: #334155;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #38bdf8;
            --primary-hover: #0ea5e9;
            --danger: #f43f5e;
            --warning: #f59e0b;
            --success: #10b981;
            --badge-bg: rgba(56, 189, 248, 0.1);
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text);
            padding: 2rem 1.5rem;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
        }}
        .header-title h1 {{
            font-size: 1.75rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        .header-title p {{
            color: var(--text-muted);
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }}
        .stats {{
            display: flex;
            gap: 1rem;
        }}
        .stat-badge {{
            background-color: var(--surface);
            border: 1px solid var(--border);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .stat-badge .count {{
            font-weight: 700;
            color: var(--danger);
        }}
        .controls {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}
        .search-box {{
            flex: 1;
            min-width: 260px;
            position: relative;
        }}
        .search-box input {{
            width: 100%;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.65rem 1rem;
            color: var(--text);
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }}
        .search-box input:focus {{
            border-color: var(--primary);
        }}
        .filter-pills {{
            display: flex;
            gap: 0.5rem;
        }}
        .pill {{
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 0.5rem 0.85rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
        }}
        .pill:hover, .pill.active {{
            background: var(--primary);
            color: #000;
            font-weight: 600;
            border-color: var(--primary);
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 1rem;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1.25rem 1.5rem;
            transition: transform 0.15s, border-color 0.15s;
        }}
        .card:hover {{
            border-color: var(--surface-hover);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 0.75rem;
        }}
        .folder-title {{
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--primary);
            word-break: break-word;
        }}
        .type-tag {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-weight: 700;
        }}
        .type-tag.title_mismatch {{ background: rgba(245, 158, 11, 0.2); color: var(--warning); }}
        .type-tag.not_found {{ background: rgba(244, 63, 94, 0.2); color: var(--danger); }}
        .type-tag.download_failed {{ background: rgba(244, 63, 94, 0.2); color: var(--danger); }}
        .card-body {{
            font-size: 0.95rem;
            color: var(--text);
            margin-bottom: 1rem;
        }}
        .suggestion-box {{
            background: rgba(15, 23, 42, 0.6);
            border-left: 3px solid var(--warning);
            padding: 0.75rem 1rem;
            border-radius: 0 6px 6px 0;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        }}
        .suggestion-box strong {{
            color: var(--warning);
        }}
        .card-actions {{
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.45rem 0.85rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 500;
            text-decoration: none;
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background: var(--primary);
            color: #000;
        }}
        .btn-primary:hover {{
            background: var(--primary-hover);
        }}
        .btn-secondary {{
            background: var(--surface-hover);
            color: var(--text);
            border-color: var(--border);
        }}
        .btn-secondary:hover {{
            background: #475569;
        }}
        .empty-state {{
            text-align: center;
            padding: 4rem 1rem;
            color: var(--text-muted);
        }}
        .copy-toast {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--success);
            color: #fff;
            padding: 0.65rem 1.25rem;
            border-radius: 6px;
            font-size: 0.9rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }}
        .copy-toast.show {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>⚠ Anime Refresher - Action Required</h1>
                <p>The following folders could not be automatically processed and require attention.</p>
            </div>
            <div class="stats">
                <div class="stat-badge">
                    <span>Pending Items:</span>
                    <span class="count" id="errorCount">{len(self.errors)}</span>
                </div>
            </div>
        </header>

        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Filter anime folders or errors...">
            </div>
            <div class="filter-pills">
                <button class="pill active" data-filter="all">All ({len(self.errors)})</button>
                <button class="pill" data-filter="title_mismatch">Title Mismatch</button>
                <button class="pill" data-filter="not_found">Not Found</button>
            </div>
        </div>

        <div class="grid" id="errorGrid">
            <!-- Rendered dynamically via JavaScript -->
        </div>

        <div class="empty-state" id="emptyState" style="display: none;">
            <h2>🎉 No matching error records found</h2>
            <p>Try adjusting your search filter.</p>
        </div>
    </div>

    <div class="copy-toast" id="copyToast">Copied to clipboard!</div>

    <script>
        const ERRORS_DATA = {errors_json};

        let currentFilter = 'all';
        let searchQuery = '';

        function renderErrors() {{
            const grid = document.getElementById('errorGrid');
            const emptyState = document.getElementById('emptyState');
            grid.innerHTML = '';

            const filtered = ERRORS_DATA.filter(item => {{
                const matchesFilter = currentFilter === 'all' || item.error_type === currentFilter;
                const matchesSearch = item.folder_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                      item.closest_candidate.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                      item.human_message.toLowerCase().includes(searchQuery.toLowerCase());
                return matchesFilter && matchesSearch;
            }});

            if (filtered.length === 0) {{
                emptyState.style.display = 'block';
                return;
            }} else {{
                emptyState.style.display = 'none';
            }}

            filtered.forEach(item => {{
                const card = document.createElement('div');
                card.className = 'card';

                const badgeText = item.error_type === 'title_mismatch' ? 'Title Mismatch' :
                                  item.error_type === 'not_found' ? 'Not Found' : 'Download Error';

                card.innerHTML = `
                    <div class="card-header">
                        <div class="folder-title">${{escapeHtml(item.folder_name)}}</div>
                        <span class="type-tag ${{item.error_type}}">${{badgeText}}</span>
                    </div>
                    <div class="card-body">
                        <p>${{escapeHtml(item.human_message)}}</p>
                    </div>
                    <div class="suggestion-box">
                        <strong>Action Needed:</strong> ${{escapeHtml(item.suggested_action)}}
                    </div>
                    <div class="card-actions">
                        <a href="${{item.animepahe_search_url}}" target="_blank" rel="noopener noreferrer" class="btn btn-primary">
                            🔍 Search on Animepahe
                        </a>
                        ${{item.closest_candidate && item.closest_candidate !== 'None found' && item.closest_candidate !== 'N/A' ? `
                            <button class="btn btn-secondary" onclick="copyToClipboard('${{escapeHtml(item.closest_candidate)}}')">
                                📋 Copy Suggested Name
                            </button>
                        ` : ''}}
                    </div>
                `;
                grid.appendChild(card);
            }});
        }}

        function escapeHtml(str) {{
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }}

        function copyToClipboard(text) {{
            navigator.clipboard.writeText(text).then(() => {{
                const toast = document.getElementById('copyToast');
                toast.textContent = `Copied "${{text}}" to clipboard!`;
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 2500);
            }});
        }}

        document.getElementById('searchInput').addEventListener('input', (e) => {{
            searchQuery = e.target.value;
            renderErrors();
        }});

        document.querySelectorAll('.pill').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderErrors();
            }});
        }});

        // Initial Render
        renderErrors();
    </script>
</body>
</html>
"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html_content, encoding="utf-8")
            logger.info(f"Generated interactive error report at: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write HTML error report: {e}")
            return False

# Global reporter instance
error_reporter = ErrorReporter()
