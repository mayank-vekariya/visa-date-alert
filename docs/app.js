const input = document.querySelector("#message-input");
const analyzeButton = document.querySelector("#analyze-button");
const resultPanel = document.querySelector("#lab-result");
const resultLevel = document.querySelector("#result-level");
const resultScore = document.querySelector("#result-score");
const scoreFill = document.querySelector("#score-fill");
const reasonList = document.querySelector("#reason-list");

const visaTerms = [
  "b2",
  "b-2",
  "b1/b2",
  "b1 b2",
  "visitor visa",
  "tourist visa",
];
const excludedVisaTerms = [
  "b1", "b-1", "h1b", "h-1b", "h1", "h-1", "h4", "h-4",
  "f1", "f-1", "l1", "l-1", "o1", "o-1", "j1", "j-1",
];
const locations = [
  "mumbai",
  "delhi",
  "hyderabad",
  "chennai",
  "kolkata",
  "mum",
  "del",
  "hyd",
  "chn",
  "kol",
];
const months = [
  "january", "february", "march", "april", "may", "june", "july", "august",
  "september", "october", "november", "december", "jan", "feb", "mar", "apr",
  "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
];

function normalize(value) {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase()
    .replace(/[^\p{L}\p{N}_\s/?:+\-]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function escapeRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function hasTerm(text, term) {
  const escaped = escapeRegex(term).replace(/\s+/g, "\\s+");
  return new RegExp(`(^|[^\\p{L}\\p{N}_])${escaped}(?![\\p{L}\\p{N}_])`, "u").test(text);
}

function detect(rawText) {
  const text = normalize(rawText);
  if (!text) {
    return { level: "LOW", score: 0, reasons: ["empty message"] };
  }

  const hardNegatives = [
    [/\bn\/?a\b/, "not-available abbreviation"],
    [/\bno (?:(?:open|available) )?(?:appointments?|dates?|slots?)\b/, "explicit no-slots statement"],
    [/\b(?:slots?|appointments?|dates?) (?:are )?not (?:open|available)\b/, "explicit not-open statement"],
    [/\bnothing (?:is )?available\b/, "nothing available"],
    [/\b(?:slots?|appointments?) (?:are )?closed\b/, "slots closed"],
    [/\b(?:all )?(?:slots?|dates?) (?:are )?(?:gone|booked)\b/, "slots already gone"],
    [/\b(?:no (?:submit button|consular)|not able to (?:book|schedule|submit))\b/, "reported appointment cannot be submitted"],
    [/\b(?:(?:dm|inbox|ping|contact) me|agents?|low charges|pay after)\b/, "promotional or agent message"],
  ];

  for (const [pattern, reason] of hardNegatives) {
    if (pattern.test(text)) {
      return { level: "LOW", score: 0, reasons: [reason] };
    }
  }

  let score = 0;
  const reasons = [];
  const visa = visaTerms.find((term) => hasTerm(text, term));
  const excludedVisa = excludedVisaTerms.find((term) => hasTerm(text, term));
  if (excludedVisa && !visa) {
    return {
      level: "LOW",
      score: 0,
      reasons: [`non-target visa category (${excludedVisa.toUpperCase()})`],
    };
  }
  const positivePatterns = [
    [/\bslots? (?:(?:are|have) )?open(?:ed)?\b/, 5, "slot-open phrase"],
    [/\b(?:slots?|appointments?) (?:are )?available\b/, 5, "appointment available"],
    [/\bdates? (?:are )?available\b/, 4, "date available"],
    [/\bbulk (?:appointments?|dates?|slots?)\b/, 5, "bulk slot report"],
    [/\b(?:new|fresh) dates?\b/, 4, "new dates"],
    [/\bbook (?:it )?now\b/, 3, "book now"],
    [/\bavailable (?:right )?now\b/, 4, "available now"],
    [/\b(?:still|currently) available\b/, 4, "currently available"],
    [/\b(?:yes|go) (?:\d+ )?(?:all|mum|del|hyd|chn|kol)\b/, 5, "compact availability report"],
  ];
  const matches = positivePatterns.filter(([pattern]) => pattern.test(text));
  if (matches.length) {
    const strongest = matches.sort((a, b) => b[1] - a[1])[0];
    score += strongest[1];
    reasons.push(`+${strongest[1]} ${strongest[2]}`);
  }

  if (visa) {
    score += 2;
    reasons.push(`+2 target visa (${visa.toUpperCase()})`);
  }
  const location = locations.find((term) => hasTerm(text, term));
  if (location) {
    score += 1;
    reasons.push(`+1 target location (${location})`);
  }
  const month = months.find((term) => hasTerm(text, term));

  if (!matches.length && /\bopen(?:ed)?\b/.test(text) && location) {
    score += 4;
    reasons.push("+4 target location reported open");
  }

  if (!matches.length && /\bavailable\b/.test(text)) {
    if (/\b(?:appointments?|consular|ofc|slots?|vac)\b/.test(text)) {
      score += 5;
      reasons.push("+5 appointment context reported available");
    } else if (visa || location || month) {
      score += 4;
      reasons.push("+4 targeted availability report");
    }
  }

  const urgency = ["hurry", "urgent", "asap", "go check", "check now", "right now"].find(
    (word) => text.includes(word),
  );
  if (urgency) {
    score += 2;
    reasons.push(`+2 urgency (${urgency})`);
  }

  if (month) {
    score += 1;
    reasons.push("+1 appointment month");
  }

  if (/\b(?:was|were) (?:open|available)\b|\bopened (?:earlier|yesterday|last night)\b/.test(text)) {
    score -= 6;
    reasons.push("-6 past or expired report");
  }
  if (text.includes("?")) {
    score -= 2;
    reasons.push("-2 question mark");
  }
  if (
    /\bwhen (?:will|do|are)\b|\b(?:anyone|somebody) (?:see|saw|know|check)\b|\bcan (?:anyone|someone|somebody)\b|\bany\b.*\b(?:appointments?|dates?|slots?)\b/.test(text)
  ) {
    score -= 4;
    reasons.push("-4 information-seeking question");
  }

  score = Math.max(score, 0);
  const level = score >= 9 ? "HIGH" : score >= 5 ? "MEDIUM" : "LOW";
  return { level, score, reasons: reasons.length ? reasons : ["no slot signal"] };
}

function render(result) {
  resultPanel.classList.remove("low", "medium", "high");
  resultPanel.classList.add(result.level.toLocaleLowerCase());
  resultLevel.textContent = result.level;
  resultScore.textContent = String(result.score);
  scoreFill.style.width = `${Math.min((result.score / 12) * 100, 100)}%`;
  reasonList.replaceChildren();
  result.reasons.forEach((reason) => {
    const item = document.createElement("li");
    item.textContent = reason;
    reasonList.append(item);
  });
}

function analyze() {
  render(detect(input.value));
}

analyzeButton.addEventListener("click", analyze);
document.querySelectorAll("[data-message]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.message;
    analyze();
    input.focus();
  });
});

document.querySelector("#year").textContent = String(new Date().getFullYear());
analyze();
