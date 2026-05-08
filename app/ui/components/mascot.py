import base64
import os

from app.ui.styles import theme

_MASCOT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "static", "mascot.png")
)
# Streamlit static serving URL (enableStaticServing = true 설정 필요)
_MASCOT_URL = "/app/static/mascot.png"


def get_mascot_img_tag(size: int = 60, expression: str = "happy") -> str:
    if os.path.exists(_MASCOT_PATH):
        return (
            f'<div style="width:{size}px;height:{size}px;flex-shrink:0;">'
            f'<img src="{_MASCOT_URL}" '
            f'style="width:100%;height:100%;object-fit:contain;border-radius:12px;display:block;"/>'
            f'</div>'
        )
    # 파일 없으면 SVG 마스코트 fallback
    svg = _build_cat_svg(size)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return (
        f'<div style="width:{size}px;height:{size}px;flex-shrink:0;">'
        f'<img src="data:image/svg+xml;base64,{b64}" '
        f'style="width:100%;height:100%;display:block;"/>'
        f'</div>'
    )


def _build_cat_svg(size: int) -> str:
    acc = theme.ACCENT
    acc_dark = theme.ACCENT_DARK
    face = theme.MASCOT_FACE
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="17" cy="20" rx="10" ry="12" fill="{acc}" transform="rotate(-12 17 20)"/>
  <ellipse cx="63" cy="20" rx="10" ry="12" fill="{acc}" transform="rotate(12 63 20)"/>
  <ellipse cx="17" cy="21" rx="6" ry="7.5" fill="#f9a8d4" transform="rotate(-12 17 21)"/>
  <ellipse cx="63" cy="21" rx="6" ry="7.5" fill="#f9a8d4" transform="rotate(12 63 21)"/>
  <circle cx="40" cy="43" r="29" fill="{face}"/>
  <path d="M12,39 Q40,12 68,39" stroke="{acc_dark}" stroke-width="5" fill="none" stroke-linecap="round"/>
  <circle cx="11" cy="43" r="9" fill="{acc_dark}"/>
  <circle cx="11" cy="43" r="6" fill="{acc}"/>
  <circle cx="11" cy="43" r="2.8" fill="{acc_dark}"/>
  <circle cx="69" cy="43" r="9" fill="{acc_dark}"/>
  <circle cx="69" cy="43" r="6" fill="{acc}"/>
  <circle cx="69" cy="43" r="2.8" fill="{acc_dark}"/>
  <ellipse cx="29" cy="40" rx="7" ry="8" fill="#1e1b4b"/>
  <circle cx="32" cy="36" r="3" fill="white"/>
  <circle cx="27" cy="43.5" r="1.3" fill="rgba(255,255,255,0.65)"/>
  <ellipse cx="51" cy="40" rx="7" ry="8" fill="#1e1b4b"/>
  <circle cx="54" cy="36" r="3" fill="white"/>
  <circle cx="49" cy="43.5" r="1.3" fill="rgba(255,255,255,0.65)"/>
  <path d="M37.5,50 C37.5,48 40,47 40,49 C40,47 42.5,48 42.5,50 Q40,53 40,53 Z" fill="#f9a8d4"/>
  <path d="M30,54 Q35,61 40,57 Q45,61 50,54" stroke="#7c3aed" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <ellipse cx="18" cy="54" rx="10" ry="7" fill="rgba(244,114,182,0.28)"/>
  <ellipse cx="62" cy="54" rx="10" ry="7" fill="rgba(244,114,182,0.28)"/>
</svg>"""
