"""Fake UP (PeopleSoft Fluid) portal for adapter testing.

Login flow:
  / → (new-application form → captcha → alert → stays on /) → (login form) → /wizard

Wizard is a single-page app with left-nav section <li> items.
  _goto_section clicks a <li> whose text starts with the section name.
  _save_section clicks #UP_FAE_WRK_SAVE_PB (no alert → saved).

Sections:
  Personal Information, Contact Details, Demographic Details,
  Tertiary Education, Secondary Education, Study Choice,
  General Details, Documentation

upload_documents:
  _goto_section("Documentation") → upload anchors → ptModFrame → modal
"""

from aiohttp import web

_PIXEL_GIF = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x21,
    0xF9, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3B,
])

# UP captcha: UP_L_{CHAR}_{n}.JPG → lowercase char
_CAPTCHA_CODE = "pqrstu"
_CAPTCHA_IMAGES = [f"UP_L_{c.upper()}_{i+1}.JPG" for i, c in enumerate(_CAPTCHA_CODE)]

# ---------------------------------------------------------------------------
# Initial page (handles both new-application and login)
# ---------------------------------------------------------------------------

def _initial_page() -> str:
    imgs = "".join(
        f'<img alt="Image{i+1}" src="/captcha/{fname}" style="width:30px;height:30px">\n'
        for i, fname in enumerate(_CAPTCHA_IMAGES)
    )
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>UP Online Application</title></head>
<body>
<h1>UP Online Application Portal</h1>

<!-- "I want to" select — adapter selects "start new application" then "login" -->
<p>
  <label for="i-want-to">I want to</label>
  <select id="i-want-to" onchange="showSection(this.value)">
    <option value="">--</option>
    <option>start new application</option>
    <option>login to continue / view study application</option>
  </select>
</p>

<!-- New application form -->
<div id="new-app-section">
  <h2>New Application</h2>
  <p><label for="career-select">Career of Study</label>
    <select id="career-select">
      <option value="">--</option>
      <option>Undergraduate</option><option>Postgraduate</option>
    </select></p>
  <p><label for="first-year-select">First Year of Study</label>
    <select id="first-year-select">
      <option value="">--</option>
      <option>2026</option><option>2027</option>
    </select></p>
  <p><label>Last Name
    <input id="last-name" type="text"></label></p>
  <p><label>First Name
    <input id="first-name" type="text"></label></p>
  <p><label>Email Address
    <input id="email" type="email"></label></p>
  <p><label>Confirm Email Address
    <input id="confirm-email" type="email"></label></p>
  <p><label>Date of Birth
    <input id="UP_OAP_WRK_BIRTHDATE" type="date"></label></p>
  <p><label for="id-type">Identify me by</label>
    <select id="id-type">
      <option value="">--</option>
      <option>SA ID Number</option><option>Passport</option>
    </select></p>
  <p><label>South African National ID
    <input id="sa-id" type="text"></label></p>
  <p>Security code:</p>
  {imgs}
  <p><label>*Security Code (case sensitive)
    <input id="security-code" type="text"></label></p>
  <p>
    <!-- alert dialog shown after clicking Go on new-application form -->
    <div id="new-app-alert" role="alertdialog" style="display:none;border:2px solid orange;padding:8px">
      Your application details sent to your email address.
      <button onclick="dismissNewAppAlert()">OK</button>
    </div>
    <button type="button" id="go-new-app" onclick="submitNewApp()">Go</button>
  </p>
</div>

<!-- Login form -->
<div id="login-section">
  <h2>Login</h2>
  <p><label>Application ID
    <input id="login-app-id" type="text"></label></p>
  <p><label>Password
    <input id="login-password" type="password"></label></p>
  <p>
    <button type="button" id="go-login" onclick="submitLogin()">Go</button>
  </p>
</div>

<script>
function showSection(v) {{
  // Toggle which form (and its 'Go' button) is visible, so click_button('Go')
  // resolves to a single button — the real portal switches forms here too.
  var newApp = document.getElementById('new-app-section');
  var login = document.getElementById('login-section');
  if (v === 'start new application') {{
    newApp.style.display = ''; login.style.display = 'none';
  }} else if (v && v.indexOf('login') === 0) {{
    newApp.style.display = 'none'; login.style.display = '';
  }}
}}
function submitNewApp() {{
  document.getElementById('new-app-alert').style.display = '';
}}
function dismissNewAppAlert() {{
  document.getElementById('new-app-alert').style.display = 'none';
}}
function submitLogin() {{
  location.href = '/wizard';
}}
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# _select_by_label helpers
# The adapter fills these via label text matching. We use <label>+<select>/<input>
# pairs.  Both sections are visible at once; adapter fills whichever it finds.
# ---------------------------------------------------------------------------

_SUBJ_OPTS = ("<option value=''>--</option>"
              "<option>Mathematics</option>"
              "<option>English Home Language</option>"
              "<option>Life Orientation</option>"
              "<option>Physical Sciences</option>"
              "<option>Accounting</option>"
              "<option>Geography</option>"
              "<option>History</option>")

# NSC achievement levels (1-7) for the CRSE_GRADE_INPUT$n select
_LEVEL_OPTS = "<option value=''>--</option>" + "".join(
    f"<option>{lvl}</option>" for lvl in range(1, 8)
)
# Percentage band for the CRSE_GRADE_OFF$n select
_PCT_OPTS = "<option value=''>--</option>" + "".join(
    f"<option>{pct}</option>" for pct in range(30, 101)
)

_WIZARD_PAGE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>UP Application Wizard</title></head>
<body>
<!-- _in_wizard checks for "Overall Application Status" -->
<p>Overall Application Status: In Progress</p>

<!-- Left-nav sections — _goto_section clicks <li> whose text starts with section name -->
<ul id="left-nav">
  <li onclick="showSection('personal')">Personal Information</li>
  <li onclick="showSection('contact')">Contact Details</li>
  <li onclick="showSection('demo')">Demographic Details</li>
  <li onclick="showSection('tertiary')">Tertiary Education</li>
  <li onclick="showSection('secondary')">Secondary Education</li>
  <li onclick="showSection('choice')">Study Choice</li>
  <li onclick="showSection('general')">General Details</li>
  <li onclick="showSection('docs')">Documentation</li>
</ul>

<!-- Toolbar Save/Next buttons (UP uses these instead of Save/Next pattern) -->
<button type="button" id="UP_FAE_WRK_SAVE_PB" onclick="void(0)">Save</button>
<button type="button" id="UP_FAE_WRK_NEXT_PB" onclick="void(0)">Next</button>

<!-- ------------------------------------------------------------------ -->
<!-- Personal Information -->
<!-- ------------------------------------------------------------------ -->
<section id="personal">
  <h2>Personal Information</h2>
  <p><label for="up-title">Title</label>
    <select id="up-title">
      <option value="">--</option><option>Mr</option><option>Ms</option>
      <option>Mrs</option><option>Dr</option>
    </select></p>
  <p><label>Preferred First Name
    <input id="up-preferred" type="text"></label></p>
</section>

<!-- ------------------------------------------------------------------ -->
<!-- Contact Details -->
<!-- ------------------------------------------------------------------ -->
<section id="contact">
  <h2>Contact Details</h2>
  <p><label>Address Line 1
    <input id="up-addr1" type="text"></label></p>
  <p><label>Mobile Number
    <input id="up-mobile" type="text"></label></p>
  <!-- City/Postcode modal trigger — _click_labeled matches aria-label/title -->
  <p><label for="up-city-btn">Select City / Postcode</label>
    <button type="button" id="up-city-btn" title="Select City / Postcode"
      aria-label="Select City / Postcode" onclick="openPostcodeModal()">Search</button></p>
</section>

<!-- ------------------------------------------------------------------ -->
<!-- Demographic Details -->
<!-- ------------------------------------------------------------------ -->
<section id="demo">
  <h2>Demographic Details</h2>
  <p><label for="up-gender">Gender</label>
    <select id="up-gender">
      <option value="">--</option><option>Male</option><option>Female</option>
    </select></p>
  <p><label for="up-lang">Home Language</label>
    <select id="up-lang">
      <option value="">--</option>
      <option>English</option><option>Afrikaans</option><option>isiZulu</option>
    </select></p>
  <p><label for="up-popgrp">Population Group</label>
    <select id="up-popgrp">
      <option value="">--</option>
      <option>Black</option><option>Coloured</option>
      <option>Indian/Asian</option><option>White</option>
    </select></p>
  <p><label for="up-tellmore">Tell us more</label>
    <select id="up-tellmore">
      <option value="">--</option>
      <option>South African Black</option><option>Other</option>
    </select></p>
</section>

<!-- ------------------------------------------------------------------ -->
<!-- Tertiary Education -->
<!-- ------------------------------------------------------------------ -->
<section id="tertiary">
  <h2>Tertiary Education</h2>
  <p><label for="up-tertiary-prev">Were you prev enrolled at a University, a Univ of Technology or a Post School Technical College?</label>
    <select id="up-tertiary-prev">
      <option value="">--</option>
      <option>No</option><option>Yes</option>
    </select></p>
</section>

<!-- ------------------------------------------------------------------ -->
<!-- Secondary Education -->
<!-- ------------------------------------------------------------------ -->
<section id="secondary">
  <h2>Secondary Education</h2>
  <p><label for="up-school-year">Final School Year</label>
    <select id="up-school-year">
      <option value="">--</option>
      <option>2024</option><option>2023</option>
    </select></p>
  <p><label for="up-authority">Examining Authority</label>
    <select id="up-authority">
      <option value="">--</option>
      <option>DBE (NSC)</option><option>IEB</option>
    </select></p>
  <p><label>Examination Number
    <input id="up-exam-num" type="text"></label></p>
  <p><label for="up-grades-type">School Grades Type</label>
    <select id="up-grades-type">
      <option value="">--</option>
      <option>NSC</option><option>IEB</option>
    </select></p>
  <p><label for="up-highest-grade">Highest grade completed</label>
    <select id="up-highest-grade">
      <option value="">--</option>
      <option>Grade 12</option><option>Grade 11</option>
    </select></p>
  <p><label for="up-exemption">Exemption Type</label>
    <select id="up-exemption">
      <option value="">--</option>
      <option>Unconditional</option><option>Conditional</option>
    </select></p>
  <button type="button" id="Select School" onclick="void(0)">Select School</button>
  <h3>Subjects</h3>
""" + "".join(
    f"<p>"
    f"<label for='SCHOOL_CRSE_NBR${n}'>Subject {n+1}</label>"
    f"<select id='SCHOOL_CRSE_NBR${n}'>{_SUBJ_OPTS}</select>"
    f"<label for='CRSE_GRADE_INPUT${n}'>Level</label>"
    f"<select id='CRSE_GRADE_INPUT${n}'>{_LEVEL_OPTS}</select>"
    f"<label for='CRSE_GRADE_OFF${n}'>Percent</label>"
    f"<select id='CRSE_GRADE_OFF${n}'>{_PCT_OPTS}</select>"
    f"</p>"
    for n in range(7)
) + """
</section>

<!-- ------------------------------------------------------------------ -->
<!-- Study Choice -->
<!-- ------------------------------------------------------------------ -->
<section id="choice">
  <h2>Study Choice</h2>
  <!-- _pick_choice clicks the opener → search modal → picks a row → the chosen
       programme lands in the hidden CHOICE value input the adapter reads back -->
  <button type="button" id="UP_FAE_WRK_CHANGE_CODE"
    onclick="openChoiceModal()">Add Choice 1</button>
  <button type="button" id="UP_FAE_WRK_CHANGE_CODE_ATP"
    onclick="openChoiceModal()">Add Choice 2</button>
  <input type="hidden" id="UP_FAE_WRK_UP_CHOICE1">
  <input type="hidden" id="UP_FAE_WRK_UP_CHOICE2">
</section>

<!-- ------------------------------------------------------------------ -->
<!-- General Details -->
<!-- ------------------------------------------------------------------ -->
<section id="general">
  <h2>General Details</h2>
  <p><label for="UP_FAE_STG_GENL_UP_HOUSING_OPT">Apply for Residence</label>
    <select id="UP_FAE_STG_GENL_UP_HOUSING_OPT">
      <option value="">--</option><option>No</option><option>Yes</option>
    </select></p>
  <p><label><input type="checkbox" id="UP_FAE_STG_GENL_UP_NSFAS">
    Applying for NSFAS?</label></p>
  <p><label><input type="checkbox" id="UP_FAE_STG_GENL_UP_FIN_AID">
    Applying for financial aid?</label></p>
</section>

<!-- ------------------------------------------------------------------ -->
<!-- Documentation -->
<!-- ------------------------------------------------------------------ -->
<section id="docs">
  <h2>Documentation</h2>
  <button type="button" id='UP_FAE_WRK_FILE_CREATE1_LBL$0' onclick="openUploadModal(0)">
    Add ID Copy</button>
  <button type="button" id='UP_FAE_WRK_FILE_CREATE1_LBL$2' onclick="openUploadModal(2)">
    Add Grade 11 Results</button>
</section>

<!-- Postcode modal placeholder -->
<div id="postcode-modal" style="display:none;border:2px solid blue;padding:8px">
  <p>Postcode Search Results</p>
  <table>
    <tr>
      <td><button id="SELECT_BTN$0" type="button" onclick="selectPostcode()">Select</button></td>
      <td>SOWETO street code | Johannesburg | 1804 | Gauteng</td>
    </tr>
  </table>
</div>

<script>
function showSection(name) { /* all sections always visible */ }

function openPostcodeModal() {
  var existing = document.querySelector('iframe[name^="ptModFrame"]');
  if (existing) existing.remove();
  var f = document.createElement('iframe');
  f.name = 'ptModFrame_0'; f.src = '/modal/postcode';
  f.style.cssText = 'position:fixed;top:50px;left:50px;width:600px;height:300px;' +
    'z-index:9999;background:white;border:2px solid #333';
  document.body.appendChild(f);
}

function openUploadModal(n) {
  var existing = document.querySelector('iframe[name^="ptModFrame"]');
  if (existing) existing.remove();
  var f = document.createElement('iframe');
  f.name = 'ptModFrame_' + n; f.src = '/modal/upload-up';
  f.style.cssText = 'position:fixed;top:50px;left:50px;width:500px;height:300px;' +
    'z-index:9999;background:white;border:2px solid #333';
  document.body.appendChild(f);
}

function openChoiceModal() {
  var existing = document.querySelector('iframe[name^="ptModFrame"]');
  if (existing) existing.remove();
  var f = document.createElement('iframe');
  f.name = 'ptModFrame_0'; f.src = '/modal/choice';
  f.style.cssText = 'position:fixed;top:50px;left:50px;width:600px;height:300px;' +
    'z-index:9999;background:white;border:2px solid #333';
  document.body.appendChild(f);
}
</script>
</body>
</html>"""

_POSTCODE_MODAL = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<form name="win0">
<h3>Postcode Search</h3>
<input type="text" id="UP_POSTSRCH_WRK_SEARCH_KEY">
<button type="button" id="UP_POSTSRCH_WRK_SEARCH_BTN" onclick="void(0)">Search</button>
<table>
  <tr>
    <td>
      <button id="SELECT_BTN$0" type="button" onclick="pick()">Select</button>
    </td>
    <td>SOWETO street code | Johannesburg | 1804 | Gauteng</td>
  </tr>
</table>
</form>
<script>
// The adapter runs `submitAction_win0(document.win0, id)` to search; the result
// row is already in the table, so this is a no-op that just must exist.
function submitAction_win0(form, id) {}
function pick() {
  // Deferred removal so the adapter's js_click(SELECT) evaluate returns before
  // the iframe detaches (see the other fakes for the rationale).
  setTimeout(function() {
    try {
      window.parent.document.querySelectorAll('iframe[name^="ptModFrame"]')
          .forEach(function(f) { f.remove(); });
    } catch(e) {}
  }, 50);
}
</script>
</body>
</html>"""

_CHOICE_MODAL = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<form name="win0">
<h3>Programme Search</h3>
<input type="text" id="UP_FAE_WRK_SEARCH_KEY">
<button type="button" id="UP_OAP_WRK_SEARCH_BTN" onclick="void(0)">Search</button>
<table>
  <tr>
    <td><button id="SELECT_BTN$0" type="button"
      onclick="pick('Computer Science Open BSc 3 years')">Select</button></td>
    <td>Computer Science Open BSc 3 years</td>
  </tr>
  <tr>
    <td><button id="SELECT_BTN$1" type="button"
      onclick="pick('Information Systems Open BSc 3 years')">Select</button></td>
    <td>Information Systems Open BSc 3 years</td>
  </tr>
</table>
</form>
<script>
function submitAction_win0(form, id) {}
function pick(text) {
  // Record the chosen programme in the first empty CHOICE input (the adapter
  // reads it back to confirm the selection), then close the modal (deferred).
  try {
    var doc = window.parent.document;
    var c1 = doc.querySelector('#UP_FAE_WRK_UP_CHOICE1');
    var c2 = doc.querySelector('#UP_FAE_WRK_UP_CHOICE2');
    if (c1 && !c1.value) { c1.value = text; }
    else if (c2) { c2.value = text; }
  } catch(e) {}
  setTimeout(function() {
    try {
      window.parent.document.querySelectorAll('iframe[name^="ptModFrame"]')
          .forEach(function(f) { f.remove(); });
    } catch(e) {}
  }, 50);
}
</script>
</body>
</html>"""

_UP_UPLOAD_MODAL = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<h3>File Attachment</h3>
<input type="file" id="fileInput" style="display:none">
<button type="button" id="PT_ATTACH_MYDEVICE"
    onclick="document.getElementById('fileInput').click()">My Device</button>
<button type="button" id="#ICUpload" onclick="showComplete()">Upload</button>
<span id="upload-complete" style="display:none">Upload Complete</span>
<button type="button" id="#ICOK" style="display:none" onclick="closeModal()">Done</button>
<script>
function showComplete() {
  document.getElementById('upload-complete').style.display = '';
  document.getElementById('#ICOK').style.display = '';
}
function closeModal() {
  // Deferred so the adapter's js_click(Done) evaluate returns before detach.
  setTimeout(function() {
    try {
      window.parent.document.querySelectorAll('iframe[name^="ptModFrame"]')
          .forEach(function(f) { f.remove(); });
    } catch(e) {}
  }, 50);
}
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def make_up_app() -> web.Application:
    app = web.Application()

    def html_handler(html: str):
        async def h(r: web.Request) -> web.Response:
            return web.Response(text=html, content_type="text/html")
        return h

    async def captcha_img(r: web.Request) -> web.Response:
        return web.Response(body=_PIXEL_GIF, content_type="image/gif")

    async def complete(r: web.Request) -> web.Response:
        html = "<html><body><h1>Application submitted (TEST MODE)</h1></body></html>"
        return web.Response(text=html, content_type="text/html")

    app.router.add_get("/", html_handler(_initial_page()))
    app.router.add_get("/wizard", html_handler(_WIZARD_PAGE))
    app.router.add_get("/captcha/{filename}", captcha_img)
    app.router.add_get("/modal/postcode", html_handler(_POSTCODE_MODAL))
    app.router.add_get("/modal/choice", html_handler(_CHOICE_MODAL))
    app.router.add_get("/modal/upload-up", html_handler(_UP_UPLOAD_MODAL))
    app.router.add_get("/complete", complete)

    return app
