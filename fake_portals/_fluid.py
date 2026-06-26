"""Shared utilities for faking PeopleSoft Fluid portals (UCT, Wits, UP).

Key Fluid behaviours we need to replicate so fluid.py helpers succeed:

  save_step()  — clicks button with text "Save", polls for "Next" to appear.
                 Fake: Save onclick hides itself and shows Next (pure JS, no
                 server round-trip needed).

  next_step()  — clicks button with text "Next", which navigates to the next
                 step page.

  js_fill()    — page.evaluate sets el.value + fires change. Works on any <input>.

  js_select_text() — finds <select> by id, sets option by text + fires change.
                     Works on any <select> with matching options.

  set_switch() — finds checkbox by id, toggles via el.click(). Works on any
                 <input type="checkbox">.

  button_visible() — finds a[role=button], input[type=button], button whose
                     textContent matches the given string AND offsetParent !== null.
                     Save/Next must satisfy this.
"""

from aiohttp import web

# JavaScript injected into every wizard step page.  Save hides itself and
# makes Next visible; Next is an anchor whose href navigates to the next step.
_SAVE_NEXT_JS = """
<script>
(function() {
  var saveBtn = document.getElementById('__save');
  var nextBtn = document.getElementById('__next');
  if (saveBtn) {
    saveBtn.addEventListener('click', function() {
      saveBtn.style.display = 'none';
      if (nextBtn) nextBtn.style.display = '';
    });
  }
})();
</script>
"""


def fluid_step(
    step_n: int,
    title: str,
    fields_html: str,
    next_url: str,
) -> str:
    """Return an HTML page for a PeopleSoft-style wizard step.

    The Save/Next pattern:
      - 'Save' button: visible on load, onclick hides self + shows Next
      - 'Next' button: hidden on load, onclick navigates to next_url
    Both are <a role="button"> so fluid.button_visible() finds them by text.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Step {step_n}: {title}</title></head>
<body>
<h1>Step {step_n} of 16: {title}</h1>
{fields_html}
<div style="margin-top:20px">
  <a id="__save" role="button" style="cursor:pointer;margin-right:12px">Save</a>
  <a id="__next" role="button" href="{next_url}"
     style="cursor:pointer;display:none">Next</a>
  <a role="button" href="javascript:history.back()"
     style="cursor:pointer;margin-left:12px">Previous</a>
</div>
{_SAVE_NEXT_JS}
</body>
</html>"""


def make_fluid_login_page(
    *,
    username_id: str,
    password_id: str,
    submit_id: str,
    action: str,
    extra_fields: str = "",
) -> str:
    """Login page with the exact IDs the adapter expects."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Login</title></head>
<body>
<h1>Online Application Login</h1>
<form action="{action}" method="post">
  <p><label>Username / ID
    <input id="{username_id}" name="{username_id}" type="text"></label></p>
  <p><label>Password
    <input id="{password_id}" name="{password_id}" type="password"></label></p>
  {extra_fields}
  <p><input id="{submit_id}" type="submit" value="Sign In"></p>
</form>
</body>
</html>"""


def step_handler(step_n: int, title: str, fields_html: str, next_url: str):
    """aiohttp GET handler for a wizard step page."""
    html = fluid_step(step_n, title, fields_html, next_url)

    async def handler(request: web.Request) -> web.Response:
        return web.Response(text=html, content_type="text/html")

    return handler


def upload_modal_html(field_for_upload: str = "upload") -> str:
    """Minimal file-upload modal iframe (ptModFrame_0).

    Sequence the UCT adapter drives:
      1. click #SCC_ATCH_WRK_ATTACHADD$0  → this iframe appears
      2. frame.get_by_role("button", name="My Device").click()
             → triggers <input type=file>
      3. page.expect_file_chooser() catches it; set_files()
      4. frame.get_by_role("button", name="Upload").click()
      5. frame.get_by_text("Upload Complete").wait_for()
      6. frame.get_by_role("button", name="Done").click()
             → removes iframe from DOM
    """
    return """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<h3>File Attachment</h3>
<input type="file" id="fileInput" style="display:none">
<button type="button" onclick="document.getElementById('fileInput').click()">My Device</button>
<button type="button" id="upload-btn" onclick="showComplete()">Upload</button>
<span id="upload-complete" style="display:none">Upload Complete</span>
<button type="button" id="done-btn" style="display:none" onclick="closeModal()">Done</button>
<script>
function showComplete() {
  document.getElementById('upload-complete').style.display = '';
  document.getElementById('done-btn').style.display = '';
}
function closeModal() {
  try {
    var iframes = window.parent.document.querySelectorAll('iframe[name^="ptModFrame"]');
    iframes.forEach(function(f) { f.remove(); });
  } catch(e) {}
}
</script>
</body>
</html>"""
