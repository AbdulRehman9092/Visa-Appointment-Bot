from seleniumbase import SB
import imaplib
import email
import time
import re
import threading
import queue
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

def check_for_access_denied(sb, url=None):
    source = sb.get_page_source()
    if "<h1>Access Denied</h1>" in source:
        msg = f"Access Denied detected at {url or sb.get_current_url()}"
        print(f"[ERROR] {msg}")
        raise RuntimeError("ACCESS_DENIED")
    








def check_for_empty_response(sb, url=None):
    source = sb.get_page_source()
    if ("This page isn’t working" in source) or ("This page isn't working" in source):
        target = url or sb.get_current_url()
        print(f"[ERROR] ERR_EMPTY_RESPONSE detected at {target}")
        raise RuntimeError("ERR_EMPTY_RESPONSE")











def check_for_403(sb):
    """If the page source contains <h1>403 Forbidden</h1>, log, quit, and raise."""
    source = sb.get_page_source()
    if "<h1>403 Forbidden</h1>" in source:
        print("[ERROR] Detected 403 Forbidden – switching proxy")
        raise RuntimeError("403_FORBIDDEN")










def check_for_502(sb):
    """If the page source contains <h1>502 Bad Gateway</h1>, log, quit, and raise."""
    source = sb.get_page_source()
    if "<h1>502 Bad Gateway</h1>" in source:
        print("[ERROR] Detected Bad Gateway – switching proxy")
        raise RuntimeError("502_Bad_Gateway")









TUNNEL_RETRIES = 2

def safe_open(sb, url, retries=TUNNEL_RETRIES):
    for attempt in range(retries + 1):
        try:
            sb.open(url)
            check_for_403(sb)
            check_for_access_denied(sb)
            check_for_empty_response(sb)
            check_for_502(sb)
            return
        except Exception as e:
            msg = str(e)
            if "ERR_TUNNEL_CONNECTION_FAILED" in msg:
                if attempt < retries:
                    print(f"[Warning] Tunnel error on open, retrying open ({attempt+1}/{retries})…")
                    sb.sleep(1)
                    continue
                else:
                    # Final failure
                    raise RuntimeError("TUNNEL_FAILED")
            else:
                # Some other exception: re-raise it
                raise










def handle_login_type(sb):
    try:
        sb.execute_script("""
        // grab all inputs under any div.mb-3
const inputs = document.querySelectorAll('div.mb-3 input');

// find the first one that actually takes up space on the page
const visible = Array.from(inputs).find(el =>
  el.offsetWidth  > 0 &&
  el.offsetHeight > 0
);

if (visible) {
  visible.value = 'youremail';
  // if the site listens for JS events to enable buttons, fire one:
  visible.dispatchEvent(new Event('input', { bubbles: true }));
} else {
  console.warn('No visible input found!');
}

        """)
        sb.click("button#btnVerify")
    except Exception as e:
        print(f"[Warning] handle_login_type error: {e}")
        try:
            safe_open(sb, sb.get_current_url())
        except Exception as e2:
            print(f"[Error] Failed to refresh page: {e2}")
        return









def handle_logincaptcha_type(sb):
    try:
        sb.execute_script("""
        // grab all inputs under any div.mb-3
const inputs = document.querySelectorAll('div.mb-3 input');

// find the first one that actually takes up space on the page
const visible = Array.from(inputs).find(el =>
  el.offsetWidth  > 0 &&
  el.offsetHeight > 0
);

if (visible) {
  visible.value = 'yourPassword';
  // if the site listens for JS events to enable buttons, fire one:
  visible.dispatchEvent(new Event('input', { bubbles: true }));
} else {
  console.warn('No visible input found!');
}

        """)
        handle_captcha(sb)
    except Exception as e:
        print(f"[Warning] handle_logincaptcha_type error: {e}")
        try:
            safe_open(sb, sb.get_current_url())
        except Exception as e2:
            print(f"[Error] Failed to refresh page: {e2}")
        return









def handle_captcha(sb):
    try:
        sb.save_screenshot(r"C:\aa.png", selector="#captcha-main-div")
        answer = solve_captcha()
        print("Captcha Answer:", answer)
        digits = re.findall(r"\d", answer)
        numbers = [int(d) for d in digits]

        js_script = '''
(function(answerPositions){
  const images = document.querySelectorAll('.captcha-img');
  const visible = Array.from(images).filter(img => {
    const style = window.getComputedStyle(img);
    if (style.display==='none' || style.visibility==='hidden' || parseFloat(style.opacity)===0) return false;
    const r = img.getBoundingClientRect();
    if (r.width===0 || r.height===0) return false;
    const cx = r.left + r.width/2, cy = r.top + r.height/2;
    const el = document.elementFromPoint(cx, cy);
    return el===img || img.contains(el);
  });
  const sorted = visible.slice().sort((a,b)=>{
    const ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect();
    if (Math.abs(ra.top-rb.top)>5) return ra.top-rb.top;
    return ra.left-rb.left;
  });
  answerPositions.forEach((pos,i)=>{
    if (pos<sorted.length) setTimeout(()=>sorted[pos].click(), i*100);
  });
})(arguments[0]);'''
        
        sb.execute_script(js_script, numbers)
        sb.sleep(len(numbers)*0.35 + 0.5)
        sb.sleep(0.2)
        sb.click("button#btnVerify")

    except Exception as e:
        # Log error and refresh to retry
        print(f"[Warning] handle_captcha error: {e}")
        try:
            safe_open(sb, sb.get_current_url())
        except Exception as e2:
            print(f"[Error] Failed to refresh page: {e2}")
        # Let the main loop detect URL and retry next handler
        return





_task_queue = queue.Queue()
_result_queue = queue.Queue()



def _captcha_solver_loop():
    while True:
        
        try:
            with SB() as solver_sb:
                solver_sb.open("https://www.easemate.ai/webapp/chat?from=math-solver")
                image_path = _task_queue.get()
                if image_path is None:
                    return

                try:
                    solver_sb.send_keys("input[type='file']", image_path, timeout=30)
                    solver_sb.type(
                    'textarea[placeholder="Ask me anything…"]',
                    (
                        "The captcha has 3x3 grid which are in rows starting from top left corner. the first row from left to right direction has 0 1 2. 1st row 1st column is 0, 1st row 2nd column is 1 and 1st row 3rd column is 2.then in same way from left to right direction 2nd row 1st column is 3, 2nd row 2nd column is 4, 2nd row 3rd column is 5 . and then in same way from left to right direction 3rd row 1st column is 6, 3rd row 2nd column is 7, 3rd row 3rd column is 8. Now analyze each box 1 by 1 and store answer. if you think any box contains a faded similar digits.  Analyze it deeply first and then.make a decision. and then select it according to that decision made. Rethink and Reconsider boxes numbers and then give me answer after thinking twice. now solve and give me answer in numbers only. dont write anything else in last line answer, just numbers. Do your progress and thinking and take your time. Just answer without commas and dashes and spaces and anything."
                    )
                )
                    solver_sb.wait_for_element_not_visible("div.progress-ring", timeout=30)
                    solver_sb.click("button.css-1wchz4a.ant-btn.ant-btn-primary.custom-button")
                    solver_sb.wait_for_element("div.flex.items-center.cursor-pointer", timeout=30)
                    elems = solver_sb.find_elements("div.chat-message-row.ai .md-editor-preview p")
                    answer = elems[-1].text
                    _result_queue.put(answer)
                except Exception as e:
                    _result_queue.put(RuntimeError(f"Solver error: {e}"))
        except Exception as outer:
            _result_queue.put(RuntimeError(f"Outer solver init error: {outer}"))


_solver_thread = threading.Thread(target=_captcha_solver_loop, daemon=True)
_solver_thread.start()


def solve_captcha():
    # Send current screenshot path to solver thread
    image_path = r"C:\\aa.png"
    _task_queue.put(image_path)
    # Wait for result with timeout
    try:
        answer = _result_queue.get(timeout=60)
    except queue.Empty:
        raise TimeoutError("Captcha solver did not respond in time.")
    if isinstance(answer, Exception):
        raise answer
    return answer









def handle_visa_type(sb):
    try:
        sb.execute_script("""
            (async function(){
            // ordered [ label, exactText ]
            var pickList = [
                ["Location",    "Lahore"],
                ["Category",    "Normal"],
                ["Visa Type",   "National Visa"],
                ["Visa Sub Type","Study"]
            ];

            for (let [lbl, want] of pickList) {
                // find the one wrapper whose label matches
                var $wrapper = $("span.k-widget.k-dropdown:visible").filter(function(){
                return $("#" + $(this).attr("aria-labelledby"))
                        .text().replace(/\\*/g,"").trim() === lbl;
                }).first();
                if (!$wrapper.length) continue;

                var ddl = $wrapper.find("input[data-role='dropdownlist']")
                                .data("kendoDropDownList");
                if (!ddl) continue;

                // small pause before opening
                await new Promise(r => setTimeout(r, 100));

                // open dropdown
                $wrapper.find(".k-select").click();

                // wait for list to render
                await new Promise(r => setTimeout(r, 100));

                var $list = $("ul.k-list:visible").first();
                if (!$list.length) { ddl.close(); continue; }

                var $item = $list.find("li").filter(function(){
                return $(this).text().trim() === want;
                }).first();

                if (!$item.length) { ddl.close(); continue; }

                // click the item
                $item.get(0).click();

                // close & fire change
                ddl.close();
                ddl.trigger("change");

                // small pause before next iteration
                await new Promise(r => setTimeout(r, 100));
            }
            })();
            """)
        sb.sleep(2)
        sb.click("button#btnSubmit")
    except Exception as e:
        print(f"[Warning] handle_visa_type error: {e}")
        try:
            safe_open(sb, sb.get_current_url())
        except Exception as e2:
            print(f"[Error] Failed to refresh page: {e2}")
        return
    








def handle_slot_type(sb):
    try:
        sb.wait_for_element_visible("button#btnSubmit", timeout=20)
        sb.execute_script("""
    (function() {
    // 1) Click whichever calendar‐icon toggle is currently visible:
    const toggles = Array.from(
        document.querySelectorAll('span[role="button"][aria-label="select"]')
    );
    const visibleToggle = toggles.find(el => el.offsetParent !== null);
    if (!visibleToggle) {
        console.warn('No visible calendar toggle found.');
        return;
    }
    visibleToggle.click();
    console.log('Opened the calendar.');

    // 2) Advance “Next” until it becomes disabled:
    let nextBtn = document.querySelector('a[data-action="next"][role="button"]');
    if (!nextBtn) {
        console.warn('Could not find <a data-action="next"> after opening.');
        return;
    }
    while (!nextBtn.classList.contains('k-state-disabled')) {
        nextBtn.click();
        console.log('  → Clicked Next');
        // Re‐query because Kendo re‐renders on each click
        nextBtn = document.querySelector('a[data-action="next"][role="button"]');
        if (!nextBtn) break;
    }
    console.log('"Next" is now disabled.');

    // 3) Wait 600 ms before reading header & selecting a day:
    setTimeout(() => {
        // 3a) Read the header (e.g. “July 2025”) to know which month/year is showing
        const headerButton = document.querySelector('a[data-action="nav-up"]');
        if (!headerButton) {
        console.warn('Could not find the month/year header (nav-up).');
        return;
        }
        const headerText = headerButton.textContent.trim();
        const m = headerText.match(/^([A-Za-z]+)\s+(\d{4})$/);
        if (!m) {
        console.warn('Unexpected header text format:', headerText);
        return;
        }
        const monthName = m[1];
        const year = parseInt(m[2], 10);

        // Build a lookup from full month names → 1–12
        const monthNames = [
        'January','February','March','April','May','June',
        'July','August','September','October','November','December'
        ];
        const monthIndex = monthNames.indexOf(monthName) + 1; 
        if (monthIndex <= 0) {
        console.warn('Unrecognized month name:', monthName);
        return;
        }
        // Kendo’s data-value uses zero-based month: Jan→0, Feb→1, … Dec→11
        const kendoMonthNumber = monthIndex - 1;
        console.log(`Detected calendar is showing: ${monthName} ${year} (kendoMonthNumber=${kendoMonthNumber})`);

        // 3b) Grab the <table role="grid"> and all its day‐<a> elements
        const calendarTable = document.querySelector('table[role="grid"]');
        if (!calendarTable) {
        console.warn('Could not find <table role="grid">.');
        return;
        }
        const allDayLinks = Array.from(
        calendarTable.querySelectorAll('td[role="gridcell"] > a[data-value]')
        );

        // 3c) Filter to those whose data‐value’s month/year matches exactly
        const sameMonthLinks = allDayLinks.filter(a => {
        const [yStr, mStr] = a.getAttribute('data-value').split('/');
        const y = parseInt(yStr, 10);
        const m = parseInt(mStr, 10);
        return y === year && m === kendoMonthNumber;
        });
        console.log('All same‐month <a> tags:', sameMonthLinks.map(a => a.textContent.trim()).join(', '));
        if (sameMonthLinks.length === 0) {
        console.warn('No days found for', monthName, year);
        return;
        }

        // 3d) From those same‐month links, filter out any whose parent <td> is disabled
        const enabledLinks = sameMonthLinks.filter(a => {
        const td = a.closest('td[role="gridcell"]');
        return td && !td.classList.contains('k-state-disabled');
        });
        console.log('Selectable days this month:', enabledLinks.map(a => a.textContent.trim()).join(', '));
        if (enabledLinks.length === 0) {
        console.warn('No selectable days in', monthName, year);
        return;
        }

        // 3e) Parse each link’s day‐number, pick the maximum, then click it
        let maxDay = -1;
        let linkToClick = null;
        enabledLinks.forEach(a => {
        const dayNum = parseInt(a.getAttribute('data-value').split('/')[2], 10);
        if (dayNum > maxDay) {
            maxDay = dayNum;
            linkToClick = a;
        }
        });

        if (!linkToClick) {
        console.warn('Could not determine which link to click.');
        return;
        }
        // Click after a tiny extra pause to ensure the grid is stable:
        setTimeout(() => {
        linkToClick.click();
        console.log(`✔ Clicked ${monthName} ${maxDay}, ${year}`);
        }, 200);

    }, 600);
    })();
    """)
        sb.sleep(3)
        sb.execute_script("""
            (function() {
    // 1) Grab all dropdown‐toggles (role="listbox") and pick the one that is currently visible:
    const allToggles = Array.from(
        document.querySelectorAll('span[role="listbox"]')
    );
    const visibleToggle = allToggles.find(el => el.offsetParent !== null);
    if (!visibleToggle) {
        console.warn('No visible <span role="listbox"> found.');
        return;
    }

    // 2) Click it to open the popup
    visibleToggle.click();
    console.log('Opened the visible slot‐dropdown.');

    // 3) After a short delay (to allow the listbox to render), pick the last clickable slot:
    setTimeout(() => {
        // Now that the dropdown is open, all <li role="option"> belong to that popup.
        // We reverse() so that we start from the bottom.
        const allOptions = Array.from(
        document.querySelectorAll('li[role="option"]')
        ).reverse();

        for (const li of allOptions) {
        const slotDiv = li.querySelector('div');
        if (!slotDiv) continue;

        // If its inline style has “pointer” (meaning it’s enabled/clickable), click it
        if (slotDiv.style.cursor === 'pointer') {
            slotDiv.click();
            console.log('Clicked slot:', slotDiv.textContent.trim());
            break;
        }
        }
    }, 500);
    })();

            """)

        sb.sleep(2)
        sb.click("button#btnSubmit")
    except Exception as e:
            print(f"[Warning] handle_slot_type error: {e}")
            try:
                safe_open(sb, sb.get_current_url())
            except Exception as e2:
                print(f"[Error] Failed to refresh page: {e2}")
            return









def imap():
    """
    Connects to the Gmail IMAP server, fetches the most recent unread email,
    extracts a 6-digit OTP (if present), marks the email as read, and returns the OTP.
    Returns None if no OTP is found or if there are no unread messages.
    """

    IMAP_HOST = "imap.gmail.com"
    IMAP_PORT = 993
    USERNAME = "email"
    PASSWORD = "app_password"

    # --- Connect and Login ---
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(USERNAME, PASSWORD)
    mail.select("inbox")

    # --- Search for UNSEEN (unread) emails ---
    status, messages = mail.search(None, '(UNSEEN)')
    if status != "OK" or not messages[0].split():
        # No unread messages
        mail.logout()
        return None

    # --- Get the latest unread email ID ---
    email_ids = messages[0].split()
    latest_email_id = email_ids[-1]

    # --- Fetch the latest unread email ---
    status, data = mail.fetch(latest_email_id, "(RFC822)")
    if status != "OK":
        mail.logout()
        return None

    raw_email = data[0][1]

    # --- Parse email ---
    msg = email.message_from_bytes(raw_email)
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                body = part.get_payload(decode=True).decode(errors="ignore")
                break
    else:
        body = msg.get_payload(decode=True).decode(errors="ignore")

    # --- Extract OTP using regex (6-digit sequence) ---
    otp_match = re.search(r'\b(\d{6})\b', body)
    otp = otp_match.group(1) if otp_match else None

    # --- Mark email as SEEN (read) ---
    mail.store(latest_email_id, '+FLAGS', '\\Seen')

    # --- Logout and return OTP ---
    mail.logout()
    return otp









def handle_datafill_type(sb):
    try:
        sb.wait_for_element_visible("//button[text()='I agree to provide my consent']", timeout=20)
        sb.scroll_to("//button[text()='I agree to provide my consent']")
        sb.click("//button[text()='I agree to provide my consent']")
        sb.send_keys("input#uploadfile-1", r"C:\pic.png")
        sb.click("//button[text()='Understood']")
        sb.sleep(5)
        otp = imap()
        sb.sleep(5)
        sb.type("input#EmailCode", otp)
        sb.wait_for_element_present("input#TravelDate", timeout=10)
        sb.type("input#TravelDate", "2025-09-15")
        sb.type("input#IntendedDateOfArrival", "2025-09-15")
        sb.type("input#IntendedDateOfDeparture", "2025-09-16")
        sb.click("input.rdo-applicant")
        sb.sleep(1)
        sb.click("button#btnSubmit")
    except Exception as e:
        print(f"[Warning] handle_datafill_type error: {e}")
        try:
            safe_open(sb, sb.get_current_url())
        except Exception as e2:
            print(f"[Error] Failed to refresh page: {e2}")
        return









def handle_payment_type(sb):
    try:
        sb.wait_for_element_visible("button#btnPayAmount", timeout=20)
        sb.click("button#btnPayAmount")
        sb.click("//button[text()='Accept']")
        sb.sleep(50)
        otp = imap()
        sb.sleep(5)
        sb.type("input#MobileCode", otp)
        sb.click("//button[text()='Submit']")
    except Exception as e:
        print(f"[Warning] handle_payment_type error: {e}")
        try:
            safe_open(sb, sb.get_current_url())
        except Exception as e2:
            print(f"[Error] Failed to refresh page: {e2}")
        return
    








def handle_merchant_type(sb):
    try:
        sb.wait_for_element_visible("input#btnPay", timeout=25)
        sb.driver.switch_to.active_element.send_keys(Keys.TAB)
        sb.driver.switch_to.active_element.send_keys("cardNumber")
        sb.driver.switch_to.active_element.send_keys(Keys.TAB)
        sb.sleep(1)
        sb.execute_script("""
        // 1. OPEN the MONTH dropdown
        var monthDropdownInput = document.querySelector("#ExpiryMonthText input.select-dropdown");
        monthDropdownInput.click();

        // 2. FIND the “August” <li><span>…</span></li> and click it
        //    (Note: the UL has class="dropdown-content select-dropdown")
        var monthItems = document.querySelectorAll("#ExpiryMonthText ul.dropdown-content.select-dropdown li span");
        monthItems.forEach(function(span){
        if (span.textContent.trim() === "month here") {
            span.click();
        }
        });

        // 3. OPEN the YEAR dropdown
        var yearDropdownInput = document.querySelector("#ExpiryYearText input.select-dropdown");
        yearDropdownInput.click();

        // 4. FIND the “3030” <li><span>…</span></li> and click it
        var yearItems = document.querySelectorAll("#ExpiryYearText ul.dropdown-content.select-dropdown li span");
        yearItems.forEach(function(span){
        if (span.textContent.trim() === "expiry year here") {
            span.click();
        }
        });
        """)
        sb.sleep(1)
        sb.execute_script("""
        // 1. Grab the CVV input by its ID
        var cvvInput = document.getElementById("ValidationCode");

        // 2. Set its value to "999"
        cvvInput.value = "cvv value here";

        // 3. Dispatch an "input" event so Angular/JS bindings pick up the change
        cvvInput.dispatchEvent(new Event("input"));

        // 4. (Optional) If there’s a key-press or key-up listener, fire a “keyup” event
        cvvInput.dispatchEvent(new KeyboardEvent("keyup", { key: "0" }));
        """)
        sb.sleep(2)
        sb.click("input#btnPay")
    except Exception as e:
        print(f"[Warning] handle_merchant_type error: {e}")
        try:
            safe_open(sb, sb.get_current_url())
        except Exception as e2:
            print(f"[Error] Failed to refresh page: {e2}")
        return







def handle_sadapay_type(sb):
    try:
        sb.wait_for_element_visible("input#inputID", timeout=20)
        sb.sleep(50)
        otp = imap()
        sb.sleep(5)
        sb.type("input#inputID", otp)
        sb.click("button#sendOtp")
        sb.sleep(25)
    except Exception as e:
        print(f"[Warning] handle_sadapay_type error: {e}")
        try:
            safe_open(sb, sb.get_current_url())
        except Exception as e2:
            print(f"[Error] Failed to refresh page: {e2}")
        return
    








proxies = [

]

while True:
    with SB() as sb:
        try:
            sb.maximize_window()
            while True:
                try:
                    safe_open(sb, "https://appointment.theitalyvisa.com/Global/home/index")
                except RuntimeError as tunnel_err:
                    print(f"[Error] net::ERR_TUNNEL_CONNECTION_FAILED with this proxy, rotating…")
                    break
                try:
                    sb.wait_for_element_visible('a[href="/Global/appointment/newappointment"]', timeout=25)
                    sb.click('a[href="/Global/appointment/newappointment"]', timeout=30)
                except Exception as e:
                    print(f"[Warning] Timeout or error on new appointment link: {e}")
                    try:
                        sb.open(sb.get_current_url())
                    except Exception as refresh_err:
                        print(f"[Error] Failed to refresh after timeout: {refresh_err}")
                    continue

                for check_count in range(50):
                        current_url = sb.get_current_url()
                        if "appointmentcaptcha" in current_url:
                            handle_captcha(sb)
                        elif "AppointmentCaptcha" in current_url:
                            handle_captcha(sb)
                        elif "NewAppointment?" in current_url:
                            safe_open(sb, "https://appointment.theitalyvisa.com/Global/home/index")
                        elif "Global/home/index" in current_url:
                            try:
                                sb.wait_for_element_visible('a[href="/Global/appointment/newappointment"]', timeout=25)
                                sb.click('a[href="/Global/appointment/newappointment"]', timeout=30)
                            except Exception as e:
                                print(f"[Warning] Timeout or error on new appointment link: {e}")
                                try:
                                    safe_open(sb, sb.get_current_url())
                                except Exception as refresh_err:
                                    print(f"[Error] Failed to refresh after timeout: {refresh_err}")
                                continue
                        elif "VisaType" in current_url:
                            handle_visa_type(sb)
                        elif "visatype" in current_url:
                            handle_visa_type(sb)
                        elif "logincaptcha" in current_url:
                            handle_logincaptcha_type(sb)
                        elif "LoginCaptcha" in current_url:
                            handle_logincaptcha_type(sb)
                        elif "Login?" in current_url:
                            handle_login_type(sb)
                        elif "LogIn?" in current_url:
                            handle_login_type(sb)
                        elif "login?" in current_url:
                            handle_login_type(sb)
                        elif "SlotSelection" in current_url:
                            handle_slot_type(sb)
                        elif "Slotselection" in current_url:
                            handle_slot_type(sb)
                        elif "slotselection" in current_url:
                            handle_slot_type(sb)
                        elif "pendingappointment" in current_url:
                            sb.wait_for_element_visible("button.btn-primary", timeout=20)
                            sb.click("button.btn-primary")
                        elif "ApplicantSelection" in current_url:
                            handle_datafill_type(sb)
                        elif "applicantselection" in current_url:
                            handle_datafill_type(sb)
                        elif "Appointment/Payment" in current_url:
                            handle_payment_type(sb)
                        elif "Appointment/payment" in current_url:
                            handle_payment_type(sb)
                        elif "MerchantPay" in current_url:
                            handle_merchant_type(sb)
                        elif "merchantpay" in current_url:
                            handle_merchant_type(sb)
                        elif "acssecure" in current_url:
                            handle_sadapay_type(sb)
                        
                    
                    # Check for slots availability
                        try:
                            sb.assert_exact_text("Appointment slots are not available", "div#div-main div", timeout=0.5)
                            print("Slots not available - restarting checks (same browser)")
                            break                     # ← breaks only out of for
                        except:
                            continue

        except RuntimeError as e:
                code = str(e)
                if code in ("403_FORBIDDEN", "ACCESS_DENIED", "ERR_EMPTY_RESPONSE", "TUNNEL_FAILED", "502_Bad_Gateway"):
                    print(f"[INFO] Caught {code}, rotating proxy…")
                    continue
                raise

        except Exception as e4:
            sb.save_screenshot("error.png")
            print(f"Error occurred: {e4}")
            continue  # restart outer while with new browser 

    time.sleep(0.2)