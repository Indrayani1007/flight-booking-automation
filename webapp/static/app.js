/**
 * app.js — SkyBook Flight Booking Application Logic
 *
 * Responsibilities:
 *  1. Flight search form validation and routing (index → results)
 *  2. Async search results loading simulation (2-second spinner)
 *  3. Dynamic flight card generation from a JSON dataset
 *  4. Checkout modal: realistic fare breakdown (base + tax + fees)
 *  5. Booking confirmation with generated reference number
 */

"use strict";

/* ──────────────────────────────────────────────────────────────
   1. FLIGHT DATASET
   ──────────────────────────────────────────────────────────── */

const FLIGHTS = [
  { id: "SK101", airline: "SkyWings Airlines",  dep: "New York",      dest: "London",       depTime: "08:30", arrTime: "20:45", duration: "7h 15m", stops: "Non-stop", basePrice: 489, aircraft: "Boeing 787" },
  { id: "SK202", airline: "Aurora Air",          dep: "New York",      dest: "London",       depTime: "14:00", arrTime: "02:10+1", duration: "7h 10m", stops: "Non-stop", basePrice: 412, aircraft: "Airbus A350" },
  { id: "SK303", airline: "Pacific Star",        dep: "Los Angeles",   dest: "Tokyo",        depTime: "11:20", arrTime: "15:40+1", duration: "11h 20m", stops: "Non-stop", basePrice: 732, aircraft: "Boeing 777" },
  { id: "SK404", airline: "Horizon Airways",     dep: "Los Angeles",   dest: "Tokyo",        depTime: "22:55", arrTime: "05:10+2", duration: "11h 15m", stops: "Non-stop", basePrice: 698, aircraft: "Airbus A380" },
  { id: "SK505", airline: "EagleJet",            dep: "Chicago",       dest: "Paris",        depTime: "17:45", arrTime: "09:30+1", duration: "8h 45m", stops: "Non-stop", basePrice: 554, aircraft: "Boeing 787" },
  { id: "SK606", airline: "BlueSky Express",     dep: "Chicago",       dest: "Paris",        depTime: "09:10", arrTime: "01:05+1", duration: "8h 55m", stops: "1 stop",    basePrice: 398, aircraft: "Airbus A321" },
  { id: "SK707", airline: "SkyWings Airlines",  dep: "Miami",         dest: "Dubai",        depTime: "23:15", arrTime: "22:00+1", duration: "13h 45m", stops: "Non-stop", basePrice: 879, aircraft: "Boeing 777" },
  { id: "SK808", airline: "Meridian Air",        dep: "Miami",         dest: "Dubai",        depTime: "10:00", arrTime: "06:30+1", duration: "14h 30m", stops: "1 stop",    basePrice: 634, aircraft: "Airbus A350" },
  { id: "SK909", airline: "NorthStar Air",       dep: "Boston",        dest: "Amsterdam",    depTime: "19:30", arrTime: "09:15+1", duration: "7h 45m", stops: "Non-stop", basePrice: 501, aircraft: "Boeing 787" },
  { id: "SK110", airline: "Atlantic Wings",      dep: "Boston",        dest: "Amsterdam",    depTime: "07:15", arrTime: "21:00", duration: "7h 45m", stops: "Non-stop", basePrice: 468, aircraft: "Airbus A330" },
  { id: "SK111", airline: "SunRise Airways",     dep: "San Francisco", dest: "Singapore",    depTime: "01:00", arrTime: "07:35+1", duration: "17h 35m", stops: "Non-stop", basePrice: 945, aircraft: "Airbus A350" },
  { id: "SK112", airline: "Pacific Star",        dep: "San Francisco", dest: "Singapore",    depTime: "13:30", arrTime: "21:40+1", duration: "17h 10m", stops: "1 stop",    basePrice: 762, aircraft: "Boeing 777" },
  { id: "SK113", airline: "SkyWings Airlines",  dep: "Philadelphia",  dest: "Buenos Aires", depTime: "21:45", arrTime: "14:30+1", duration: "11h 45m", stops: "Non-stop", basePrice: 618, aircraft: "Boeing 787" },
  { id: "SK114", airline: "EagleJet",            dep: "Philadelphia",  dest: "Buenos Aires", depTime: "06:20", arrTime: "23:10", duration: "11h 50m", stops: "Non-stop", basePrice: 589, aircraft: "Airbus A330" },
];

const CITIES = [...new Set([...FLIGHTS.map(f => f.dep), ...FLIGHTS.map(f => f.dest)])].sort();

/* ──────────────────────────────────────────────────────────────
   2. UTILITY HELPERS
   ──────────────────────────────────────────────────────────── */

/** Generate a random alphanumeric booking reference */
function generateRef() {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  return "SKY-" + Array.from({ length: 6 }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
}

/** Format a number as USD currency */
function usd(n) { return "$" + n.toFixed(2); }

/**
 * Compute a realistic fare breakdown from a base price.
 * Taxes = 15% of base, fuel surcharge = $38, booking fee = $12.
 */
function calcFare(basePrice, passengers) {
  const base     = basePrice * passengers;
  const taxes    = Math.round(base * 0.15 * 100) / 100;
  const fuel     = 38 * passengers;
  const booking  = 12;
  const total    = base + taxes + fuel + booking;
  return { base, taxes, fuel, booking, total };
}

/** Retrieve query-string parameters from the current URL */
function getParam(key) {
  return new URLSearchParams(window.location.search).get(key) || "";
}

/** Persist data to sessionStorage */
function store(key, val) { sessionStorage.setItem(key, JSON.stringify(val)); }
function load(key)        { try { return JSON.parse(sessionStorage.getItem(key)); } catch { return null; } }

/* ──────────────────────────────────────────────────────────────
   3. PAGE: INDEX (index.html)
   ──────────────────────────────────────────────────────────── */

function initSearchPage() {
  const form     = document.getElementById("search-form");
  const depSel   = document.getElementById("departure");
  const destSel  = document.getElementById("destination");
  const dateIn   = document.getElementById("travel-date");
  const passIn   = document.getElementById("passengers");
  const errDiv   = document.getElementById("form-error");

  if (!form) return;  // Not on this page

  // Populate city dropdowns dynamically from the dataset
  CITIES.forEach(city => {
    [depSel, destSel].forEach(sel => {
      const opt = document.createElement("option");
      opt.value = city;
      opt.textContent = city;
      sel.appendChild(opt);
    });
  });

  // Pre-select Philadelphia / Buenos Aires as defaults (mirrors BlazeDemo behaviour)
  depSel.value  = "Philadelphia";
  destSel.value = "Buenos Aires";

  // Set minimum travel date to today
  dateIn.min   = new Date().toISOString().split("T")[0];
  dateIn.value = new Date(Date.now() + 86400000).toISOString().split("T")[0];

  form.addEventListener("submit", e => {
    e.preventDefault();
    errDiv.classList.add("hidden");

    const dep  = depSel.value;
    const dest = destSel.value;
    const date = dateIn.value;
    const pax  = parseInt(passIn.value, 10);

    // Basic validation
    if (!dep || !dest) { showError("Please select departure and destination cities."); return; }
    if (dep === dest)  { showError("Departure and destination cities must be different."); return; }
    if (!date)         { showError("Please select a travel date."); return; }
    if (pax < 1 || pax > 9) { showError("Passenger count must be between 1 and 9."); return; }

    const params = new URLSearchParams({ dep, dest, date, pax });
    window.location.href = `results.html?${params}`;
  });

  function showError(msg) {
    errDiv.textContent = msg;
    errDiv.classList.remove("hidden");
  }
}

/* ──────────────────────────────────────────────────────────────
   4. PAGE: RESULTS (results.html)
   ──────────────────────────────────────────────────────────── */

function initResultsPage() {
  const spinner    = document.getElementById("loading-spinner");
  const resultsDiv = document.getElementById("results-container");
  const summaryEl  = document.getElementById("search-summary");
  const countEl    = document.getElementById("results-count");

  if (!spinner) return;  // Not on this page

  const dep  = getParam("dep");
  const dest = getParam("dest");
  const date = getParam("date");
  const pax  = parseInt(getParam("pax"), 10) || 1;

  summaryEl.textContent = `${dep} → ${dest}  ·  ${date}  ·  ${pax} passenger${pax > 1 ? "s" : ""}`;

  // ── 2-second async spinner simulation ──
  // In a real application this delay would be an API call to a backend.
  // Here we use setTimeout to demonstrate asynchronous UI state management
  // which must be handled correctly by the Selenium WebDriverWait.
  spinner.classList.remove("hidden");
  resultsDiv.classList.add("hidden");

  setTimeout(() => {
    spinner.classList.add("hidden");

    const matches = FLIGHTS.filter(f => f.dep === dep && f.dest === dest);
    countEl.textContent = `${matches.length} flight${matches.length !== 1 ? "s" : ""} found`;

    if (matches.length === 0) {
      resultsDiv.innerHTML = `
        <div class="text-center py-16 text-gray-500">
          <div class="text-5xl mb-4">✈️</div>
          <p class="text-xl font-medium">No flights found for this route.</p>
          <p class="mt-2">Try different cities or dates.</p>
          <a href="index.html" class="mt-6 inline-block btn-primary">Search Again</a>
        </div>`;
    } else {
      resultsDiv.innerHTML = matches.map(flight => renderFlightCard(flight, pax, date)).join("");
      // Attach click handlers to all "Select" buttons
      document.querySelectorAll(".select-flight-btn").forEach(btn => {
        btn.addEventListener("click", () => selectFlight(btn.dataset.flightId, pax, date));
      });
    }

    resultsDiv.classList.remove("hidden");
  }, 2000);  // 2-second simulated API latency
}

/** Render a single flight result card */
function renderFlightCard(flight, pax, date) {
  const fare = calcFare(flight.basePrice, pax);
  return `
    <div class="flight-card" data-testid="flight-card" data-flight-id="${flight.id}">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div class="flex items-center gap-4">
          <div class="airline-logo">${flight.airline[0]}</div>
          <div>
            <p class="font-bold text-gray-800 text-lg">${flight.airline}</p>
            <p class="text-sm text-gray-500">${flight.aircraft} · ${flight.stops}</p>
          </div>
        </div>
        <div class="flex items-center gap-6 text-center">
          <div>
            <p class="text-2xl font-bold text-gray-800">${flight.depTime}</p>
            <p class="text-xs text-gray-500">${flight.dep}</p>
          </div>
          <div class="text-center">
            <div class="flex items-center gap-1 text-blue-500">
              <div class="h-px w-10 bg-blue-300"></div>
              <span class="text-xs">✈</span>
              <div class="h-px w-10 bg-blue-300"></div>
            </div>
            <p class="text-xs text-gray-400 mt-1">${flight.duration}</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-800">${flight.arrTime}</p>
            <p class="text-xs text-gray-500">${flight.dest}</p>
          </div>
        </div>
        <div class="text-right">
          <p class="text-3xl font-extrabold text-blue-600" data-testid="flight-price">${usd(fare.total)}</p>
          <p class="text-xs text-gray-400">per ${pax > 1 ? pax + " passengers" : "person"}</p>
          <button
            class="select-flight-btn mt-3 btn-primary"
            data-flight-id="${flight.id}"
            data-testid="select-btn-${flight.id}">
            Select Flight
          </button>
        </div>
      </div>
    </div>`;
}

/** Store selection and navigate to checkout */
function selectFlight(flightId, pax, date) {
  const flight = FLIGHTS.find(f => f.id === flightId);
  if (!flight) return;
  store("selectedFlight", { ...flight, pax, date });
  window.location.href = `checkout.html`;
}

/* ──────────────────────────────────────────────────────────────
   5. PAGE: CHECKOUT (checkout.html)
   ──────────────────────────────────────────────────────────── */

function initCheckoutPage() {
  const form       = document.getElementById("checkout-form");
  const summaryDiv = document.getElementById("fare-summary");

  if (!form) return;  // Not on this page

  const selection = load("selectedFlight");
  if (!selection) {
    // Guard: user navigated directly without a selection
    document.getElementById("flight-info").innerHTML =
      `<p class="text-red-500 font-medium">No flight selected. <a href="index.html" class="underline">Search again.</a></p>`;
    return;
  }

  const fare = calcFare(selection.basePrice, selection.pax);

  // Populate fare summary panel
  document.getElementById("chk-airline").textContent  = selection.airline;
  document.getElementById("chk-route").textContent    = `${selection.dep} → ${selection.dest}`;
  document.getElementById("chk-flight").textContent   = selection.id;
  document.getElementById("chk-date").textContent     = selection.date;
  document.getElementById("chk-dep-time").textContent = selection.depTime;
  document.getElementById("chk-arr-time").textContent = selection.arrTime;
  document.getElementById("chk-pax").textContent      = selection.pax;
  document.getElementById("chk-base").textContent     = usd(fare.base);
  document.getElementById("chk-taxes").textContent    = usd(fare.taxes);
  document.getElementById("chk-fuel").textContent     = usd(fare.fuel);
  document.getElementById("chk-booking").textContent  = usd(fare.booking);
  document.getElementById("chk-total").textContent    = usd(fare.total);

  // Credit card number live formatting (groups of 4)
  const ccInput = document.getElementById("cc-number");
  if (ccInput) {
    ccInput.addEventListener("input", () => {
      let v = ccInput.value.replace(/\D/g, "").slice(0, 16);
      ccInput.value = v.match(/.{1,4}/g)?.join(" ") || v;
    });
  }

  // Expiry month/year validation
  const ccExp = document.getElementById("cc-expiry");
  if (ccExp) {
    ccExp.addEventListener("input", () => {
      let v = ccExp.value.replace(/\D/g, "").slice(0, 4);
      if (v.length > 2) v = v.slice(0, 2) + "/" + v.slice(2);
      ccExp.value = v;
    });
  }

  form.addEventListener("submit", e => {
    e.preventDefault();
    if (!validateCheckoutForm()) return;

    const ref = generateRef();
    store("bookingConfirmation", {
      ref,
      airline:  selection.airline,
      route:    `${selection.dep} → ${selection.dest}`,
      flight:   selection.id,
      date:     selection.date,
      dep:      selection.depTime,
      arr:      selection.arrTime,
      pax:      selection.pax,
      total:    usd(fare.total),
      passengerName: document.getElementById("passenger-name").value.trim(),
    });

    window.location.href = `confirmation.html`;
  });
}

function validateCheckoutForm() {
  const errDiv = document.getElementById("checkout-error");
  errDiv.classList.add("hidden");

  const name  = document.getElementById("passenger-name").value.trim();
  const email = document.getElementById("passenger-email").value.trim();
  const cc    = document.getElementById("cc-number").value.replace(/\s/g, "");
  const exp   = document.getElementById("cc-expiry").value;
  const cvv   = document.getElementById("cc-cvv").value;

  if (!name)              { showChkError("Full name is required."); return false; }
  if (!email.includes("@")) { showChkError("Valid email address is required."); return false; }
  if (cc.length < 13)    { showChkError("Please enter a valid card number (13–16 digits)."); return false; }
  if (!/^\d{2}\/\d{2}$/.test(exp)) { showChkError("Expiry must be MM/YY format."); return false; }
  if (!/^\d{3,4}$/.test(cvv)) { showChkError("CVV must be 3 or 4 digits."); return false; }

  return true;

  function showChkError(msg) {
    errDiv.textContent = msg;
    errDiv.classList.remove("hidden");
  }
}

/* ──────────────────────────────────────────────────────────────
   6. PAGE: CONFIRMATION (confirmation.html)
   ──────────────────────────────────────────────────────────── */

function initConfirmationPage() {
  const wrap = document.getElementById("confirmation-wrap");
  if (!wrap) return;

  const booking = load("bookingConfirmation");
  if (!booking) {
    wrap.innerHTML = `<p class="text-red-500 text-center py-10">No booking found. <a href="index.html" class="underline">Start over.</a></p>`;
    return;
  }

  document.getElementById("conf-ref").textContent     = booking.ref;
  document.getElementById("conf-name").textContent    = booking.passengerName;
  document.getElementById("conf-airline").textContent = booking.airline;
  document.getElementById("conf-route").textContent   = booking.route;
  document.getElementById("conf-flight").textContent  = booking.flight;
  document.getElementById("conf-date").textContent    = booking.date;
  document.getElementById("conf-dep").textContent     = booking.dep;
  document.getElementById("conf-arr").textContent     = booking.arr;
  document.getElementById("conf-pax").textContent     = booking.pax;
  document.getElementById("conf-total").textContent   = booking.total;
  document.getElementById("conf-status").textContent  = "CONFIRMED";

  // Clear session data to prevent back-button confusion
  sessionStorage.removeItem("selectedFlight");
}

/* ──────────────────────────────────────────────────────────────
   7. BOOTSTRAP — auto-detect page and init
   ──────────────────────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", () => {
  initSearchPage();
  initResultsPage();
  initCheckoutPage();
  initConfirmationPage();
});
