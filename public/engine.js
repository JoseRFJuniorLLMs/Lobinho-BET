// ============================================================================
// LOBINHO-BET ENGINE v2.0
// ============================================================================
// Modelos: Poisson | Dixon-Coles | ELO | Markov | Bradley-Terry
// API: The Odds API (free tier - 500 req/mes)
// Zero backend. Tudo roda no browser.
// ============================================================================

// ===================== TEAM DATABASE =====================
const TEAMS_DB = {
    flamengo:         { name:"Flamengo",           elo:1680, squad:185, atk:1.28, def:1.12, ha:0.15, gh:1.8, ga:1.4, ch:0.9, ca:1.3 },
    palmeiras:        { name:"Palmeiras",          elo:1665, squad:175, atk:1.22, def:1.18, ha:0.12, gh:1.7, ga:1.3, ch:0.8, ca:1.2 },
    corinthians:      { name:"Corinthians",        elo:1620, squad:120, atk:1.10, def:1.05, ha:0.18, gh:1.5, ga:1.1, ch:1.1, ca:1.4 },
    sao_paulo:        { name:"Sao Paulo",          elo:1610, squad:110, atk:1.08, def:1.10, ha:0.14, gh:1.4, ga:1.0, ch:1.0, ca:1.3 },
    atletico_mg:      { name:"Atletico MG",        elo:1635, squad:130, atk:1.15, def:1.08, ha:0.16, gh:1.6, ga:1.2, ch:1.0, ca:1.4 },
    botafogo:         { name:"Botafogo",           elo:1640, squad:95,  atk:1.18, def:1.05, ha:0.13, gh:1.6, ga:1.3, ch:1.1, ca:1.3 },
    fluminense:       { name:"Fluminense",         elo:1625, squad:85,  atk:1.12, def:1.10, ha:0.12, gh:1.4, ga:1.1, ch:1.0, ca:1.2 },
    gremio:           { name:"Gremio",             elo:1615, squad:90,  atk:1.10, def:1.08, ha:0.17, gh:1.5, ga:1.0, ch:0.9, ca:1.4 },
    internacional:    { name:"Internacional",      elo:1610, squad:88,  atk:1.08, def:1.12, ha:0.16, gh:1.4, ga:1.0, ch:0.9, ca:1.3 },
    cruzeiro:         { name:"Cruzeiro",           elo:1590, squad:75,  atk:1.05, def:1.02, ha:0.15, gh:1.3, ga:1.0, ch:1.1, ca:1.4 },
    vasco:            { name:"Vasco da Gama",      elo:1580, squad:60,  atk:1.02, def:1.00, ha:0.14, gh:1.2, ga:0.9, ch:1.2, ca:1.5 },
    bahia:            { name:"Bahia",              elo:1575, squad:55,  atk:1.05, def:0.98, ha:0.16, gh:1.3, ga:1.0, ch:1.1, ca:1.4 },
    fortaleza:        { name:"Fortaleza",          elo:1600, squad:50,  atk:1.10, def:1.05, ha:0.18, gh:1.4, ga:1.0, ch:0.9, ca:1.3 },
    manchester_city:  { name:"Manchester City",    elo:1920, squad:1100,atk:1.45, def:1.30, ha:0.12, gh:2.5, ga:2.1, ch:0.6, ca:0.9 },
    liverpool:        { name:"Liverpool",          elo:1880, squad:950, atk:1.40, def:1.25, ha:0.18, gh:2.3, ga:1.9, ch:0.7, ca:1.0 },
    arsenal:          { name:"Arsenal",            elo:1860, squad:900, atk:1.35, def:1.28, ha:0.14, gh:2.2, ga:1.8, ch:0.7, ca:0.9 },
    chelsea:          { name:"Chelsea",            elo:1780, squad:850, atk:1.25, def:1.15, ha:0.12, gh:1.9, ga:1.5, ch:0.9, ca:1.2 },
    manchester_united:{ name:"Manchester United",  elo:1760, squad:800, atk:1.20, def:1.10, ha:0.15, gh:1.8, ga:1.4, ch:1.0, ca:1.3 },
    tottenham:        { name:"Tottenham",          elo:1770, squad:750, atk:1.22, def:1.08, ha:0.13, gh:1.8, ga:1.5, ch:1.0, ca:1.3 },
    newcastle:        { name:"Newcastle",          elo:1750, squad:600, atk:1.18, def:1.12, ha:0.16, gh:1.7, ga:1.3, ch:0.9, ca:1.2 },
    aston_villa:      { name:"Aston Villa",        elo:1740, squad:500, atk:1.15, def:1.10, ha:0.15, gh:1.6, ga:1.2, ch:1.0, ca:1.3 },
    real_madrid:      { name:"Real Madrid",        elo:1900, squad:1050,atk:1.42, def:1.28, ha:0.15, gh:2.4, ga:2.0, ch:0.7, ca:1.0 },
    barcelona:        { name:"Barcelona",          elo:1870, squad:950, atk:1.38, def:1.20, ha:0.16, gh:2.3, ga:1.9, ch:0.8, ca:1.1 },
    atletico_madrid:  { name:"Atletico Madrid",    elo:1820, squad:600, atk:1.18, def:1.35, ha:0.14, gh:1.8, ga:1.4, ch:0.6, ca:0.9 },
    real_sociedad:    { name:"Real Sociedad",      elo:1760, squad:350, atk:1.15, def:1.10, ha:0.14, gh:1.6, ga:1.2, ch:0.9, ca:1.2 },
    sevilla:          { name:"Sevilla",            elo:1750, squad:300, atk:1.10, def:1.12, ha:0.15, gh:1.5, ga:1.1, ch:0.9, ca:1.3 },
    bayern_munich:    { name:"Bayern Munich",      elo:1910, squad:1000,atk:1.48, def:1.22, ha:0.14, gh:2.6, ga:2.2, ch:0.8, ca:1.1 },
    dortmund:         { name:"Borussia Dortmund",  elo:1820, squad:550, atk:1.32, def:1.10, ha:0.20, gh:2.2, ga:1.7, ch:1.0, ca:1.4 },
    leverkusen:       { name:"Bayer Leverkusen",   elo:1830, squad:500, atk:1.30, def:1.18, ha:0.13, gh:2.1, ga:1.7, ch:0.8, ca:1.1 },
    rb_leipzig:       { name:"RB Leipzig",         elo:1790, squad:450, atk:1.25, def:1.15, ha:0.12, gh:1.9, ga:1.5, ch:0.9, ca:1.2 },
    inter_milan:      { name:"Inter Milan",        elo:1850, squad:700, atk:1.30, def:1.32, ha:0.13, gh:2.1, ga:1.7, ch:0.6, ca:0.9 },
    ac_milan:         { name:"AC Milan",           elo:1800, squad:550, atk:1.22, def:1.18, ha:0.14, gh:1.9, ga:1.5, ch:0.8, ca:1.1 },
    juventus:         { name:"Juventus",           elo:1810, squad:580, atk:1.20, def:1.25, ha:0.15, gh:1.8, ga:1.4, ch:0.7, ca:1.0 },
    napoli:           { name:"Napoli",             elo:1820, squad:500, atk:1.28, def:1.15, ha:0.16, gh:2.0, ga:1.6, ch:0.8, ca:1.1 },
    atalanta:         { name:"Atalanta",           elo:1790, squad:400, atk:1.30, def:1.08, ha:0.14, gh:2.0, ga:1.6, ch:1.0, ca:1.3 },
    psg:              { name:"Paris Saint-Germain", elo:1870, squad:900, atk:1.42, def:1.20, ha:0.12, gh:2.4, ga:2.0, ch:0.7, ca:1.0 },
    marseille:        { name:"Olympique Marseille", elo:1750, squad:300, atk:1.15, def:1.08, ha:0.17, gh:1.6, ga:1.2, ch:1.0, ca:1.3 },
    lyon:             { name:"Olympique Lyon",     elo:1740, squad:280, atk:1.12, def:1.05, ha:0.14, gh:1.5, ga:1.2, ch:1.0, ca:1.3 },
    benfica:          { name:"Benfica",            elo:1800, squad:400, atk:1.25, def:1.15, ha:0.16, gh:2.0, ga:1.5, ch:0.8, ca:1.1 },
    porto:            { name:"FC Porto",           elo:1790, squad:350, atk:1.22, def:1.18, ha:0.17, gh:1.9, ga:1.4, ch:0.7, ca:1.1 },
    sporting:         { name:"Sporting CP",        elo:1780, squad:300, atk:1.20, def:1.12, ha:0.15, gh:1.8, ga:1.4, ch:0.8, ca:1.2 },
    ajax:             { name:"Ajax",               elo:1770, squad:320, atk:1.25, def:1.05, ha:0.15, gh:2.0, ga:1.5, ch:1.0, ca:1.3 },
    psv:              { name:"PSV",                elo:1760, squad:280, atk:1.20, def:1.10, ha:0.14, gh:1.8, ga:1.4, ch:0.9, ca:1.2 },
    river_plate:      { name:"River Plate",        elo:1700, squad:80,  atk:1.18, def:1.10, ha:0.18, gh:1.6, ga:1.2, ch:0.9, ca:1.3 },
    boca_juniors:     { name:"Boca Juniors",       elo:1690, squad:75,  atk:1.12, def:1.15, ha:0.20, gh:1.4, ga:1.0, ch:0.8, ca:1.2 },
};

const FORM_DB = {
    flamengo:"WWDWLWWDWW", palmeiras:"WDWWWLWDWW", corinthians:"LDWDLWDLWD",
    sao_paulo:"DWLDWWDLDW", atletico_mg:"WWDLWWDWLD", botafogo:"WWWDWWLDWW",
    fluminense:"DWWDLDWWDL", gremio:"WDLDWWDWLD", internacional:"DWWLDWDWWL",
    cruzeiro:"LDWDWLDWDL", manchester_city:"WWWWWDWWWW", liverpool:"WWWDWWWWDW",
    arsenal:"WWDWWWDWWW", chelsea:"WDWLDWWDLW", manchester_united:"DWLDWDWLDW",
    real_madrid:"WWWWDWWWWW", barcelona:"WWDWWWDWWL", atletico_madrid:"DDWWDWDWWD",
    bayern_munich:"WWWWWWDWWW", dortmund:"WDWWLWWDWL", inter_milan:"WWWDWWWDWW",
    ac_milan:"DWWDWLDWWD", juventus:"WDWWDWDWWD", psg:"WWWWDWWWDW",
    napoli:"WDWWWDWWDW", leverkusen:"WWWWWWWDWW", tottenham:"WDWWLDWWDL",
    newcastle:"WWDWWDWWLD", benfica:"WWWDWWDWWW", porto:"WDWWWDWWDW",
};

// Aliases para mapear nomes da API para nossas chaves
const TEAM_ALIASES = {
    'se palmeiras':'palmeiras', 'palmeiras sp':'palmeiras',
    'sc corinthians paulista':'corinthians', 'sc corinthians':'corinthians', 'corinthians sp':'corinthians',
    'sao paulo fc':'sao_paulo', 'são paulo':'sao_paulo', 'spfc':'sao_paulo', 'sao paulo sp':'sao_paulo',
    'atletico mineiro':'atletico_mg', 'club atletico mineiro':'atletico_mg', 'atletico-mg':'atletico_mg',
    'botafogo fr':'botafogo', 'botafogo rj':'botafogo',
    'fluminense fc':'fluminense', 'fluminense rj':'fluminense',
    'gremio fbpa':'gremio', 'gremio porto alegrense':'gremio',
    'sc internacional':'internacional', 'internacional rs':'internacional',
    'cruzeiro ec':'cruzeiro', 'cruzeiro mg':'cruzeiro',
    'cr vasco da gama':'vasco', 'vasco da gama':'vasco',
    'esporte clube bahia':'bahia',
    'fortaleza ec':'fortaleza', 'fortaleza ce':'fortaleza',
    'man city':'manchester_city', 'manchester city fc':'manchester_city',
    'man utd':'manchester_united', 'man united':'manchester_united', 'manchester united fc':'manchester_united',
    'liverpool fc':'liverpool',
    'arsenal fc':'arsenal',
    'chelsea fc':'chelsea',
    'tottenham hotspur':'tottenham', 'spurs':'tottenham',
    'newcastle united':'newcastle', 'newcastle utd':'newcastle',
    'aston villa fc':'aston_villa',
    'fc barcelona':'barcelona', 'fcb':'barcelona',
    'real madrid cf':'real_madrid',
    'atletico de madrid':'atletico_madrid', 'club atletico de madrid':'atletico_madrid', 'atlético madrid':'atletico_madrid', 'atlético de madrid':'atletico_madrid',
    'real sociedad de futbol':'real_sociedad',
    'sevilla fc':'sevilla',
    'fc bayern munich':'bayern_munich', 'fc bayern münchen':'bayern_munich', 'bayern münchen':'bayern_munich', 'bayern munchen':'bayern_munich',
    'borussia dortmund':'dortmund', 'bvb dortmund':'dortmund', 'bvb':'dortmund',
    'bayer 04 leverkusen':'leverkusen', 'bayer leverkusen':'leverkusen',
    'rb leipzig':'rb_leipzig', 'rasenballsport leipzig':'rb_leipzig',
    'fc internazionale':'inter_milan', 'fc internazionale milano':'inter_milan', 'inter':'inter_milan', 'inter milano':'inter_milan',
    'ac milan':'ac_milan', 'milan':'ac_milan',
    'juventus fc':'juventus',
    'ssc napoli':'napoli',
    'atalanta bc':'atalanta',
    'paris saint germain':'psg', 'paris saint-germain':'psg', 'paris sg':'psg', 'paris saint-germain fc':'psg',
    'olympique de marseille':'marseille', 'olympique marseille':'marseille', 'om':'marseille',
    'olympique lyonnais':'lyon', 'olympique lyon':'lyon', 'ol':'lyon',
    'sl benfica':'benfica', 'sport lisboa e benfica':'benfica',
    'fc porto':'porto',
    'sporting cp':'sporting', 'sporting clube de portugal':'sporting',
    'afc ajax':'ajax',
    'psv eindhoven':'psv',
    'ca river plate':'river_plate', 'river plate':'river_plate',
    'ca boca juniors':'boca_juniors', 'boca juniors':'boca_juniors', 'boca jrs':'boca_juniors',
};

// ===================== LEAGUE CONFIG =====================
const LEAGUES_CONFIG = {
    soccer_brazil_serie_a:       { name:'Brasileirão A',      flag:'🇧🇷', priority:1 },
    soccer_brazil_serie_b:       { name:'Brasileirão B',      flag:'🇧🇷', priority:2 },
    soccer_epl:                  { name:'Premier League',     flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', priority:1 },
    soccer_spain_la_liga:        { name:'La Liga',            flag:'🇪🇸', priority:1 },
    soccer_germany_bundesliga:   { name:'Bundesliga',         flag:'🇩🇪', priority:1 },
    soccer_italy_serie_a:        { name:'Serie A',            flag:'🇮🇹', priority:1 },
    soccer_france_ligue_one:     { name:'Ligue 1',            flag:'🇫🇷', priority:1 },
    soccer_uefa_champs_league:   { name:'Champions League',   flag:'🏆', priority:1 },
    soccer_uefa_europa_league:   { name:'Europa League',      flag:'🏆', priority:2 },
    soccer_conmebol_libertadores:{ name:'Libertadores',       flag:'🏆', priority:1 },
    soccer_argentina_primera_division:{ name:'Argentina Primera', flag:'🇦🇷', priority:2 },
    soccer_portugal_primeira_liga:{ name:'Primeira Liga',     flag:'🇵🇹', priority:2 },
    soccer_netherlands_eredivisie:{ name:'Eredivisie',        flag:'🇳🇱', priority:2 },
};

const DEFAULT_LEAGUES = [
    'soccer_brazil_serie_a','soccer_epl','soccer_spain_la_liga',
    'soccer_germany_bundesliga','soccer_italy_serie_a','soccer_france_ligue_one',
    'soccer_uefa_champs_league','soccer_conmebol_libertadores'
];

// ===================== TEAM NAME RESOLVER =====================
function resolveTeam(apiName) {
    const n = apiName.toLowerCase().trim();
    // Direct match
    if (TEAMS_DB[n]) return { key: n, data: TEAMS_DB[n] };
    // Alias match
    if (TEAM_ALIASES[n] && TEAMS_DB[TEAM_ALIASES[n]]) return { key: TEAM_ALIASES[n], data: TEAMS_DB[TEAM_ALIASES[n]] };
    // Underscored match
    const underscored = n.replace(/\s+/g,'_').replace(/[^a-z0-9_]/g,'');
    if (TEAMS_DB[underscored]) return { key: underscored, data: TEAMS_DB[underscored] };
    // Partial match (any DB key contained in the name or vice versa)
    for (const [key, data] of Object.entries(TEAMS_DB)) {
        const dbName = data.name.toLowerCase();
        if (n.includes(dbName) || dbName.includes(n)) return { key, data };
        if (n.includes(key.replace(/_/g,' '))) return { key, data };
    }
    // Not found - generate default from odds context
    return null;
}

function getTeamData(apiName, oddsHint) {
    const resolved = resolveTeam(apiName);
    if (resolved) return resolved.data;
    // Generate stats based on odds hint (lower odds = stronger team)
    const strength = oddsHint ? Math.max(0.5, Math.min(2.0, 2.5 / oddsHint)) : 1.0;
    return {
        name: apiName, elo: 1500 + (strength - 1) * 400,
        squad: 100 * strength, atk: strength, def: strength * 0.9,
        ha: 0.14, gh: 1.3 * strength, ga: 1.0 * strength,
        ch: 1.3 / strength, ca: 1.4 / strength,
    };
}

function getTeamForm(apiName) {
    const resolved = resolveTeam(apiName);
    if (resolved && FORM_DB[resolved.key]) return FORM_DB[resolved.key];
    return 'DDDDD';
}

// ===================== MATH HELPERS =====================
function factorial(n) {
    if (n <= 1) return 1;
    let r = 1;
    for (let i = 2; i <= n; i++) r *= i;
    return r;
}

function poissonProb(lambda, k) {
    return (Math.exp(-lambda) * Math.pow(lambda, k)) / factorial(k);
}

// ===================== MODEL 1: POISSON =====================
function poissonPredict(home, away) {
    const hl = (home.gh + away.ca) / 2 * home.atk * (1 + home.ha);
    const al = (away.ga + home.ch) / 2 * away.atk;
    let hw = 0, dr = 0, aw = 0;
    for (let h = 0; h < 8; h++) {
        for (let a = 0; a < 8; a++) {
            const p = poissonProb(hl, h) * poissonProb(al, a);
            if (h > a) hw += p; else if (h === a) dr += p; else aw += p;
        }
    }
    return { home_win: hw, draw: dr, away_win: aw, home_xg: hl, away_xg: al };
}

// ===================== MODEL 2: DIXON-COLES =====================
const RHO = -0.13;
function tau(h, a, lh, la) {
    if (h===0 && a===0) return 1 - lh*la*RHO;
    if (h===0 && a===1) return 1 + lh*RHO;
    if (h===1 && a===0) return 1 + la*RHO;
    if (h===1 && a===1) return 1 - RHO;
    return 1.0;
}

function dixonColesPredict(home, away) {
    const hl = (home.gh + away.ca) / 2 * home.atk * (1 + home.ha);
    const al = (away.ga + home.ch) / 2 * away.atk;
    let hw = 0, dr = 0, aw = 0;
    for (let h = 0; h < 8; h++) {
        for (let a = 0; a < 8; a++) {
            const p = poissonProb(hl, h) * poissonProb(al, a) * tau(h, a, hl, al);
            if (h > a) hw += p; else if (h === a) dr += p; else aw += p;
        }
    }
    const t = hw + dr + aw;
    return { home_win: hw/t, draw: dr/t, away_win: aw/t };
}

// ===================== MODEL 3: ELO =====================
function eloPredict(home, away) {
    const homeElo = home.elo + 65;
    const expHome = 1 / (1 + Math.pow(10, (away.elo - homeElo) / 400));
    const drawFactor = 0.26 - Math.abs(expHome - 0.5) * 0.2;
    let hw = expHome - drawFactor / 2;
    let aw = (1 - expHome) - drawFactor / 2;
    let dr = drawFactor;
    const t = hw + dr + aw;
    return { home_win: Math.max(0,hw/t), draw: Math.max(0,dr/t), away_win: Math.max(0,aw/t) };
}

// ===================== MODEL 4: MARKOV =====================
function formToStrength(form) {
    const w = { W:3, D:1, L:0 };
    const recent = form.slice(-5);
    let s = 0;
    for (const c of recent) s += (w[c] !== undefined ? w[c] : 1);
    if (recent.slice(-3) === 'WWW') s *= 1.2;
    if (recent.slice(-3) === 'LLL') s *= 0.8;
    return Math.max(1, s);
}

function markovPredict(homeForm, awayForm) {
    const hs = formToStrength(homeForm);
    const as_ = formToStrength(awayForm);
    const hBase = (hs / (hs + as_)) * 1.1;
    const aBase = (as_ / (hs + as_)) * 0.9;
    const hw = hBase / (hBase + aBase + 0.5) * 0.8;
    const aw = aBase / (hBase + aBase + 0.5) * 0.8;
    const dr = 1 - hw - aw;
    return { home_win: hw, draw: dr, away_win: aw };
}

// ===================== MODEL 5: BRADLEY-TERRY =====================
function bradleyTerryPredict(home, away) {
    const hs = home.squad * home.atk * (1 + home.ha);
    const as_ = away.squad * away.atk;
    const pH = hs / (hs + as_);
    const pA = as_ / (hs + as_);
    const dr = 0.25 - Math.abs(pH - 0.5) * 0.2;
    const hw = pH * (1 - dr);
    const aw = pA * (1 - dr);
    return { home_win: hw, draw: dr, away_win: aw };
}

// ===================== ENSEMBLE =====================
const WEIGHTS = { poisson:0.25, dixon_coles:0.30, elo:0.20, markov:0.15, bradley_terry:0.10 };

function ensemblePredict(homeData, awayData, homeForm, awayForm) {
    const models = {
        poisson:       poissonPredict(homeData, awayData),
        dixon_coles:   dixonColesPredict(homeData, awayData),
        elo:           eloPredict(homeData, awayData),
        markov:        markovPredict(homeForm, awayForm),
        bradley_terry: bradleyTerryPredict(homeData, awayData),
    };
    let hw = 0, dr = 0, aw = 0;
    for (const [name, pred] of Object.entries(models)) {
        const w = WEIGHTS[name] || 0.1;
        hw += pred.home_win * w;
        dr += pred.draw * w;
        aw += pred.away_win * w;
    }
    const t = hw + dr + aw;
    hw /= t; dr /= t; aw /= t;

    // xG from Poisson
    const pois = models.poisson;
    const homeXg = pois.home_xg || (homeData.gh + awayData.ca) / 2;
    const awayXg = pois.away_xg || (awayData.ga + homeData.ch) / 2;

    // Over 2.5
    const totalLambda = homeXg + awayXg;
    let under = 0;
    for (let k = 0; k < 3; k++) under += poissonProb(totalLambda, k);
    const over25 = (1 - under) * 100;

    // BTTS
    const btts = (1 - poissonProb(homeXg, 0)) * (1 - poissonProb(awayXg, 0)) * 100;

    return {
        home_win: hw, draw: dr, away_win: aw,
        home_xg: homeXg, away_xg: awayXg,
        over_25: Math.round(over25), btts: Math.round(btts),
        models,
    };
}

// ===================== VALUE DETECTOR =====================
function detectValue(prob, odds, minEdge) {
    if (!odds || odds <= 1) return null;
    const implied = 1 / odds;
    const edge = (prob * odds - 1) * 100;
    if (edge < (minEdge || 3)) return null;
    const b = odds - 1;
    const kelly = Math.max(0, ((b * prob - (1 - prob)) / b) / 4 * 100);
    const ev = prob * odds - 1;
    let confidence = 'low';
    if (edge >= 10) confidence = 'high';
    else if (edge >= 5) confidence = 'medium';
    return { edge: +edge.toFixed(1), kelly: +kelly.toFixed(1), ev: +ev.toFixed(3), confidence, implied };
}

function analyzeMatch(homeTeamName, awayTeamName, marketOdds) {
    const homeData = getTeamData(homeTeamName, marketOdds.home);
    const awayData = getTeamData(awayTeamName, marketOdds.away);
    const homeForm = getTeamForm(homeTeamName);
    const awayForm = getTeamForm(awayTeamName);

    const pred = ensemblePredict(homeData, awayData, homeForm, awayForm);

    // Value detection for each market
    const markets = [
        { key:'home', prob: pred.home_win, odds: marketOdds.home, name: homeData.name },
        { key:'draw', prob: pred.draw,     odds: marketOdds.draw, name: 'Empate' },
        { key:'away', prob: pred.away_win, odds: marketOdds.away, name: awayData.name },
    ];

    let bestValue = null;
    let bestEdge = -999;
    let signal = 'avoid';
    let bestMarket = null;

    for (const m of markets) {
        const v = detectValue(m.prob, m.odds, 3);
        if (v && v.edge > bestEdge) {
            bestEdge = v.edge;
            bestValue = v;
            bestMarket = m.key;
        }
    }

    if (bestEdge >= 8) signal = 'strong_buy';
    else if (bestEdge >= 5) signal = 'buy';
    else if (bestEdge >= 2) signal = 'hold';
    else signal = 'avoid';

    // Markov confidence (average model agreement)
    const modelPreds = Object.values(pred.models);
    const winner = pred.home_win > pred.away_win ? 'home_win' : pred.away_win > pred.home_win ? 'away_win' : 'draw';
    const agreement = modelPreds.filter(m => {
        const mWinner = m.home_win > m.away_win ? 'home_win' : m.away_win > m.home_win ? 'away_win' : 'draw';
        return mWinner === winner;
    }).length;
    const markovConfidence = Math.round((agreement / modelPreds.length) * 100);

    return {
        predictions: {
            home_win: Math.round(pred.home_win * 100),
            draw: Math.round(pred.draw * 100),
            away_win: Math.round(pred.away_win * 100),
            over_25: pred.over_25,
            btts: pred.btts,
            next_goal_home: Math.round(pred.home_xg / (pred.home_xg + pred.away_xg) * 100),
            next_goal_away: Math.round(pred.away_xg / (pred.home_xg + pred.away_xg) * 100),
        },
        edge: bestEdge > 0 ? bestEdge : 0,
        signal,
        markov_confidence: markovConfidence,
        recommended_stake: bestValue ? bestValue.kelly : 0,
        best_market: bestMarket,
        home_xg: +pred.home_xg.toFixed(2),
        away_xg: +pred.away_xg.toFixed(2),
        value_detail: bestValue,
        models: pred.models,
    };
}

// ===================== ODDS API CLIENT =====================
const ODDS_API_BASE = 'https://api.the-odds-api.com/v4';

async function fetchOddsAPI(apiKey, sport, endpoint = 'odds') {
    const params = new URLSearchParams({
        apiKey: apiKey,
        regions: 'us,uk,eu,au',
        markets: 'h2h',
        oddsFormat: 'decimal',
    });
    if (endpoint === 'scores') {
        params.delete('regions');
        params.delete('markets');
        params.delete('oddsFormat');
        params.set('daysFrom', '1');
    }
    const url = `${ODDS_API_BASE}/sports/${sport}/${endpoint}?${params}`;
    const resp = await fetch(url);
    if (!resp.ok) {
        const errText = await resp.text();
        throw new Error(`API error ${resp.status}: ${errText}`);
    }
    const remaining = resp.headers.get('x-requests-remaining');
    const used = resp.headers.get('x-requests-used');
    if (remaining !== null) {
        window._oddsApiRemaining = parseInt(remaining);
        window._oddsApiUsed = parseInt(used);
    }
    return resp.json();
}

function extractBestOdds(bookmakers) {
    let best = { home: 0, draw: 0, away: 0, home_bk: '', draw_bk: '', away_bk: '' };
    for (const bk of (bookmakers || [])) {
        for (const market of (bk.markets || [])) {
            if (market.key !== 'h2h') continue;
            for (const o of (market.outcomes || [])) {
                const name = o.name.toLowerCase();
                if (name === 'draw') {
                    if (o.price > best.draw) { best.draw = o.price; best.draw_bk = bk.title; }
                } else {
                    // First non-draw outcome = home, second = away (Odds API convention)
                    // Actually, outcomes are named by team name. First is home team.
                }
            }
            // More reliable: outcomes[0] = home, outcomes[1] = away, find draw
            const outcomes = market.outcomes || [];
            const drawOc = outcomes.find(o => o.name.toLowerCase() === 'draw');
            const nonDraw = outcomes.filter(o => o.name.toLowerCase() !== 'draw');
            if (nonDraw[0] && nonDraw[0].price > best.home) { best.home = nonDraw[0].price; best.home_bk = bk.title; }
            if (nonDraw[1] && nonDraw[1].price > best.away) { best.away = nonDraw[1].price; best.away_bk = bk.title; }
            if (drawOc && drawOc.price > best.draw) { best.draw = drawOc.price; best.draw_bk = bk.title; }
        }
    }
    return best;
}

// ===================== MAIN ENGINE =====================
async function fetchRealData(apiKey, leagues) {
    const allMatches = [];
    const errors = [];

    for (const sport of leagues) {
        try {
            const data = await fetchOddsAPI(apiKey, sport, 'odds');
            for (const match of data) {
                match._sport = sport;
                allMatches.push(match);
            }
        } catch (e) {
            errors.push({ sport, error: e.message });
            console.warn(`Error fetching ${sport}:`, e.message);
        }
    }

    return { matches: allMatches, errors };
}

function processMatch(apiMatch, index) {
    const homeTeam = apiMatch.home_team;
    const awayTeam = apiMatch.away_team;
    const bestOdds = extractBestOdds(apiMatch.bookmakers);
    const sport = apiMatch._sport;
    const leagueInfo = LEAGUES_CONFIG[sport] || { name: sport, flag: '⚽' };

    // If no odds found, skip
    if (!bestOdds.home || !bestOdds.away) return null;

    const odds = {
        home: +bestOdds.home.toFixed(2),
        draw: +bestOdds.draw.toFixed(2),
        away: +bestOdds.away.toFixed(2),
    };

    // Run analysis
    const analysis = analyzeMatch(homeTeam, awayTeam, odds);

    // Format kickoff
    const kickoff = apiMatch.commence_time
        ? new Date(apiMatch.commence_time).toLocaleTimeString('pt-BR', { hour:'2-digit', minute:'2-digit' })
        : '--:--';
    const kickoffDate = apiMatch.commence_time
        ? new Date(apiMatch.commence_time).toLocaleDateString('pt-BR', { day:'2-digit', month:'2-digit' })
        : '';

    // Build event object compatible with existing UI
    return {
        id: apiMatch.id || `match_${index}`,
        home_team: homeTeam,
        away_team: awayTeam,
        league: `${leagueInfo.flag} ${leagueInfo.name}`,
        league_raw: leagueInfo.name,
        kickoff: `${kickoffDate} ${kickoff}`,
        kickoff_ts: apiMatch.commence_time ? new Date(apiMatch.commence_time).getTime() : 0,
        odds: odds,
        edge: analysis.edge,
        signal: analysis.signal,
        markov_confidence: analysis.markov_confidence,
        recommended_stake: analysis.recommended_stake,
        is_live: false,
        predictions: analysis.predictions,
        best_market: analysis.best_market,
        home_xg: analysis.home_xg,
        away_xg: analysis.away_xg,
        value_detail: analysis.value_detail,
        best_odds_sources: {
            home: bestOdds.home_bk,
            draw: bestOdds.draw_bk,
            away: bestOdds.away_bk,
        },
        bookmaker_count: (apiMatch.bookmakers || []).length,
        form_home: getTeamForm(homeTeam).slice(-5).split(''),
        form_away: getTeamForm(awayTeam).slice(-5).split(''),
    };
}

async function runEngine(apiKey, leagues) {
    const { matches, errors } = await fetchRealData(apiKey, leagues || DEFAULT_LEAGUES);

    const processed = [];
    for (let i = 0; i < matches.length; i++) {
        const event = processMatch(matches[i], i);
        if (event) processed.push(event);
    }

    // Sort: strong_buy first, then by edge descending
    const signalOrder = { strong_buy:0, buy:1, hold:2, avoid:3 };
    processed.sort((a, b) => {
        const sa = signalOrder[a.signal] ?? 3;
        const sb = signalOrder[b.signal] ?? 3;
        if (sa !== sb) return sa - sb;
        return b.edge - a.edge;
    });

    return {
        events: processed,
        errors,
        remaining: window._oddsApiRemaining,
        used: window._oddsApiUsed,
        total: matches.length,
        valueBets: processed.filter(e => e.signal === 'buy' || e.signal === 'strong_buy').length,
    };
}

// ===================== CONFIG PERSISTENCE =====================
function saveConfig(key, value) { try { localStorage.setItem('lobinho_' + key, JSON.stringify(value)); } catch(e){} }
function loadConfig(key, def) { try { const v = localStorage.getItem('lobinho_' + key); return v ? JSON.parse(v) : def; } catch(e){ return def; } }

// ===================== EXPORTS =====================
window.LobinhoEngine = {
    runEngine,
    analyzeMatch,
    ensemblePredict,
    detectValue,
    LEAGUES_CONFIG,
    DEFAULT_LEAGUES,
    TEAMS_DB,
    saveConfig,
    loadConfig,
    resolveTeam,
};
