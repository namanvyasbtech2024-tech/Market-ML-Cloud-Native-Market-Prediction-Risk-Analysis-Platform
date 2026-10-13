document.addEventListener("DOMContentLoaded", () => {
    // --- Navigation Tabs ---
    const navItems = document.querySelectorAll(".nav-links li");
    const tabContents = document.querySelectorAll(".tab-content");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            navItems.forEach(nav => nav.classList.remove("active"));
            item.classList.add("active");
            tabContents.forEach(content => content.classList.remove("active"));
            const targetTabId = item.getAttribute("data-tab");
            document.getElementById(targetTabId).classList.add("active");
        });
    });
    
    // Test API connection
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            console.log("API Status:", data.message);
        })
        .catch(error => {
            console.error("API Error:", error);
            document.querySelector(".status-indicator .dot").style.backgroundColor = "red";
        });

    // --- State Variables ---
    let currentStockData = null;
    let currentTicker = null;
    // --- Company Info Database ---
    function updateCompanyDetails(ticker) {
        const apiTicker = ticker.replace('.NS', '');
        
        // Pseudo-random generator based on ticker string for market depth
        let seed = 0;
        for (let i = 0; i < ticker.length; i++) seed += ticker.charCodeAt(i);
        const r = (min, max) => (min + (seed % 100) / 100 * (max - min)).toFixed(2);
        
        const buyPct = parseFloat(r(40, 75));
        const sellPct = (100 - buyPct).toFixed(2);
        const elBuyPct = document.getElementById('depth-buy-pct');
        const elSellPct = document.getElementById('depth-sell-pct');
        const elBuyBar = document.getElementById('depth-buy-bar');
        const elSellBar = document.getElementById('depth-sell-bar');
        if(elBuyPct) elBuyPct.innerText = buyPct + '%';
        if(elSellPct) elSellPct.innerText = sellPct + '%';
        if(elBuyBar) elBuyBar.style.width = buyPct + '%';
        if(elSellBar) elSellBar.style.width = sellPct + '%';
        
        // Fetch Real Data from Yahoo Finance Profile API
        const aboutSection = document.getElementById('about-text');
        if (aboutSection) aboutSection.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Loading real-time company profile...';
        
        fetch(`/api/profile/${apiTicker}`)
            .then(res => res.json())
            .then(info => {
                if (aboutSection) aboutSection.innerText = info.about;
                
                const mkt = document.getElementById('fund-mktcap');
                const roe = document.getElementById('fund-roe');
                const pe = document.getElementById('fund-pe');
                const eps = document.getElementById('fund-eps');
                const div = document.getElementById('fund-div');
                const pb = document.getElementById('fund-pb');
                
                if (mkt) mkt.innerText = info.mktCap || '--';
                if (roe) roe.innerText = info.roe || '--';
                if (pe) pe.innerText = info.pe || '--';
                if (eps) eps.innerText = info.eps || '--';
                if (div) div.innerText = info.divYield || '--';
                if (pb) pb.innerText = info.pb || '--';
            })
            .catch(err => {
                console.error("Profile fetch error:", err);
                if (aboutSection) aboutSection.innerText = "Error loading company profile.";
            });
        document.getElementById('fund-indpe').innerText = r(12, 35);
        document.getElementById('fund-debt').innerText = r(0.1, 2.5);
        document.getElementById('fund-book').innerText = r(150, 1200);
        
        // Shareholding pattern
        const prom = parseFloat(r(40, 75));
        const dii = parseFloat(r(10, 30));
        const fii = parseFloat(r(5, 25));
        const pub = (100 - prom - dii - fii).toFixed(2);
        
        // Reset the active tab for shareholding UI
        document.querySelectorAll('.share-btn').forEach(b => b.classList.remove('active'));
        const firstShareBtn = document.querySelector('.share-btn[data-period="jun25"]');
        if(firstShareBtn) firstShareBtn.classList.add('active');
        const promBar = document.getElementById('share-bar-prom');
        if(promBar) {
            promBar.style.width = prom + '%';
            document.getElementById('share-pct-prom').innerText = prom + '%';
            document.getElementById('share-bar-dii').style.width = dii + '%';
            document.getElementById('share-pct-dii').innerText = dii + '%';
            document.getElementById('share-bar-fii').style.width = fii + '%';
            document.getElementById('share-pct-fii').innerText = fii + '%';
            document.getElementById('share-bar-pub').style.width = pub + '%';
            document.getElementById('share-pct-pub').innerText = pub + '%';
        }
        
        // Performance (Historical stats will be updated in fetchData where we have real prices)
        
        // Re-render Financial Performance Chart
        renderFinChart(ticker);
    }

    // --- Sub-tabs Logic ---
    document.querySelectorAll('.sub-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.sub-tab-content').forEach(c => c.classList.remove('active'));
            
            e.target.classList.add('active');
            const targetId = e.target.getAttribute('data-subtab');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // --- Financial Performance Logic ---
    const finQuarterlyData = {
        x: ['Jun \'25', 'Sep \'25', 'Dec \'25', 'Mar \'26', 'Jun \'26'],
        revenue: [290000, 290000, 300000, 320000, 346807],
        profit: [20000, 18000, 19500, 21000, 23001],
        revPct: '+5.18%',
        profPct: '+11.57%',
        label: 'JUN \'26'
    };

    const finYearlyData = {
        x: ['2022', '2023', '2024', '2025', '2026'],
        revenue: [800000, 950000, 1000000, 1150000, 1346807],
        profit: [60000, 75000, 70000, 85000, 98000],
        revPct: '+17.11%',
        profPct: '+15.29%',
        label: '2026'
    };

    function renderFinChart(ticker) {
        if (typeof ticker !== 'string') ticker = document.getElementById('stock-selector').value || 'RELIANCE.NS';
        const wrapper = document.getElementById('financial-chart');
        if(!wrapper) return;
        
        let seed = 0;
        for (let i = 0; i < ticker.length; i++) seed += ticker.charCodeAt(i);
        const r = (min, max) => min + (seed % 100) / 100 * (max - min);
        
        const isQuarterly = document.querySelector('.fin-btn[data-period="quarterly"]')?.classList.contains('active') ?? true;
        
        const periods = isQuarterly ? ['Jun \'25', 'Sep \'25', 'Dec \'25', 'Mar \'26', 'Jun \'26'] : ['2022', '2023', '2024', '2025', '2026'];
        const revBase = r(150000, 450000);
        const profBase = revBase * r(0.05, 0.15);
        
        const revData = periods.map((_, i) => revBase * (1 + (i * 0.05) + r(-0.02, 0.02)));
        const profData = periods.map((_, i) => profBase * (1 + (i * 0.08) + r(-0.05, 0.05)));
        
        const revColors = ['#30363d', '#30363d', '#30363d', '#30363d', '#a1aab5'];
        const profColors = ['#0a3622', '#0a3622', '#0a3622', '#0a3622', '#00b852'];
        
        const traceRev = {
            x: periods, y: revData,
            name: 'Revenue',
            type: 'bar',
            marker: { color: revColors },
            width: 0.25
        };
        const traceProf = {
            x: periods, y: profData,
            name: 'Profit',
            type: 'bar',
            marker: { color: profColors },
            width: 0.25
        };
        
        const layout = {
            barmode: 'group',
            bargap: 0.15,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { t: 10, r: 40, l: 10, b: 30 },
            showlegend: false,
            xaxis: { showgrid: false, tickfont: { color: '#8b949e', size: 11 } },
            yaxis: { 
                side: 'right', showgrid: true, gridcolor: '#30363d', gridwidth: 1, griddash: 'dash',
                tickfont: { color: '#8b949e', size: 11 }, tickformat: '.0s' 
            }
        };
        
        Plotly.newPlot(wrapper, [traceRev, traceProf], layout, {displayModeBar: false});
        
        const lastRev = revData[revData.length - 1];
        const lastProf = profData[profData.length - 1];
        document.getElementById('fin-revenue').innerHTML = `₹${Math.round(lastRev).toLocaleString()}<span style="font-size: 1.1rem; color: #8b949e; font-weight: normal;">Cr</span>`;
        document.getElementById('fin-profit').innerHTML = `₹${Math.round(lastProf).toLocaleString()}<span style="font-size: 1.1rem; color: #8b949e; font-weight: normal;">Cr</span>`;
    }

    const btnQuarterly = document.getElementById('btn-quarterly');
    const btnYearly = document.getElementById('btn-yearly');

    if (btnQuarterly && btnYearly) {
        btnQuarterly.addEventListener('click', () => {
            btnQuarterly.classList.add('active');
            btnYearly.classList.remove('active');
            renderFinChart(finQuarterlyData);
        });
        btnYearly.addEventListener('click', () => {
            btnYearly.classList.add('active');
            btnQuarterly.classList.remove('active');
            renderFinChart(finYearlyData);
        });

        setTimeout(() => renderFinChart(finQuarterlyData), 100);
    }

    // --- Main Chart Logic ---
    // --- Shareholding Pattern Logic ---
    const shareData = {
        'jun25': { prom: '51.10', dii: '19.50', fii: '18.20', pub: '11.20' },
        'sep25': { prom: '50.90', dii: '20.10', fii: '17.80', pub: '11.20' },
        'dec25': { prom: '50.60', dii: '20.80', fii: '17.50', pub: '11.10' },
        'mar26': { prom: '50.55', dii: '21.00', fii: '17.30', pub: '11.15' },
        'jun26': { prom: '50.48', dii: '21.19', fii: '17.20', pub: '11.13' }
    };

    const shareBtns = document.querySelectorAll('.share-btn');
    shareBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Reset all buttons
            shareBtns.forEach(b => {
                b.classList.remove('active');
                b.style.color = '#8b949e';
                b.style.border = 'none';
                b.style.padding = '0';
            });
            // Set active button styles
            const target = e.target;
            target.classList.add('active');
            target.style.color = '#fff';
            target.style.border = '1px solid #8b949e';
            target.style.padding = '4px 12px';
            target.style.borderRadius = '12px';

            // Update bars and text
            const period = target.getAttribute('data-period');
            const data = shareData[period];
            if (data) {
                document.getElementById('share-bar-prom').style.width = data.prom + '%';
                document.getElementById('share-pct-prom').innerText = data.prom + '%';
                
                document.getElementById('share-bar-dii').style.width = data.dii + '%';
                document.getElementById('share-pct-dii').innerText = data.dii + '%';
                
                document.getElementById('share-bar-fii').style.width = data.fii + '%';
                document.getElementById('share-pct-fii').innerText = data.fii + '%';
                
                document.getElementById('share-bar-pub').style.width = data.pub + '%';
                document.getElementById('share-pct-pub').innerText = data.pub + '%';
            }
        });
    });
    const stockSelector = document.getElementById('stock-selector');
    const chartTypeSelector = document.getElementById('chart-type');
    const timeframeBtns = document.querySelectorAll('.timeframe-btn');

    // Fetch available stocks
    fetch('/api/stocks')
        .then(res => res.json())
        .then(data => {
            const stocksList = Array.isArray(data) ? data : (data.stocks || []);
            
            stockSelector.innerHTML = '<option value="">Select Stock</option>';
            stocksList.forEach(stock => {
                const opt = document.createElement('option');
                opt.value = stock;
                opt.innerText = stock.replace('.NS', '');
                stockSelector.appendChild(opt);
            });
            // Auto-select ADANIPORTS if available, else first stock
            const defaultStock = stocksList.includes('ADANIPORTS.NS') ? 'ADANIPORTS.NS' : (stocksList[0] || '');
            if (defaultStock) {
                stockSelector.value = defaultStock;
                fetchAndRender(defaultStock);
            }
        })
        .catch(err => {
            console.error("Failed to load stocks:", err);
            stockSelector.innerHTML = '<option value="">Error loading stocks</option>';
        });

    stockSelector.addEventListener('change', (e) => {
        if(e.target.value) fetchAndRender(e.target.value);
    });

    chartTypeSelector.addEventListener('change', () => {
        if(currentStockData) renderPlotlyChart(currentStockData);
    });

    timeframeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            timeframeBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            updateChartTimeframe(e.target.getAttribute('data-range'));
        });
    });

    function fetchAndRender(ticker) {
        currentTicker = ticker;
        updateCompanyDetails(ticker);
        
        // Reset Model Eval Tab UI
        const lf = document.getElementById('live-forecast-container');
        if (lf) lf.style.display = 'none';

        // Reset Forecast Tab
        document.getElementById('forecast-chart').innerHTML = '<p id="forecast-placeholder" class="placeholder-text" style="text-align: center; margin-top: 200px; color: #8b949e;">Click "Generate 1-Year Prediction" to simulate the next 252 trading days.</p>';

        // Reset News Tab
        const newsCont = document.getElementById('news-feed-container');
        if (newsCont) newsCont.innerHTML = '<p class="placeholder-text" style="text-align: center; padding: 40px; color: #8b949e;">Click "Fetch Live News" to scan RSS and NewsAPI for the latest sentiment.</p>';
        const corrChart = document.getElementById('sentiment-correlation-chart');
        if (corrChart) corrChart.innerHTML = '<p class="placeholder-text" style="text-align: center; margin-top: 150px; color: #8b949e;">Click "Fetch Live News" to generate historical correlation.</p>';
        const aiCard = document.getElementById('ai-summary-card');
        if (aiCard) aiCard.style.display = 'none';
        const avgS = document.getElementById('news-avg-sentiment');
        if (avgS) { avgS.innerText = '--'; avgS.style.color = '#fff'; }
        const avgL = document.getElementById('news-sentiment-label');
        if (avgL) { avgL.innerText = '--'; avgL.style.color = '#8b949e'; }

        // Reset Backtest Tab
        const btChart = document.getElementById('backtest-chart');
        if (btChart) btChart.innerHTML = '<p id="backtest-placeholder" class="placeholder-text" style="text-align: center; margin-top: 150px; color: #8b949e;">Click "Run Backtest" to simulate the AI strategy on historical test data.</p>';
        ['bt-return', 'bt-drawdown', 'bt-winrate', 'bt-sharpe'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '--';
        });
        document.getElementById('fc-best').innerText = '--';
        document.getElementById('fc-trend').innerText = '--';
        document.getElementById('fc-worst').innerText = '--';
        const fcDate = document.getElementById('forecast-date');
        if (fcDate) fcDate.innerText = '';
        
        document.getElementById('plotly-wrapper').innerHTML = '<p class="placeholder-text" style="text-align: center; margin-top: 100px;">Loading data...</p>';
        
        const apiTicker = ticker.replace('.NS', '');
        fetch(`/api/data/${apiTicker}`)
            .then(res => res.json())
            .then(dataArray => {
                if (!Array.isArray(dataArray) || dataArray.length === 0) {
                    throw new Error("Invalid data format");
                }
                const data = {
                    dates: dataArray.map(d => d.Date),
                    open: dataArray.map(d => d.Open),
                    high: dataArray.map(d => d.High),
                    low: dataArray.map(d => d.Low),
                    close: dataArray.map(d => d.Close),
                    volume: dataArray.map(d => d.Volume),
                    SMA_20: dataArray.map(d => d.SMA_20),
                    BB_Upper: dataArray.map(d => d["BBU_20_2.0"]),
                    BB_Lower: dataArray.map(d => d["BBL_20_2.0"])
                };
                currentStockData = data;
                updateKPIs(data);
                renderPlotlyChart(data);
            })
            .catch(err => {
                console.error("Error fetching stock data:", err);
                document.getElementById('plotly-wrapper').innerHTML = '<p class="placeholder-text" style="text-align: center; margin-top: 100px; color: red;">Error loading chart data</p>';
            });
    }

    
    function updateTechnicals(data) {
        if (!data.close || data.close.length < 20) return;
        const close = data.close;
        const current = close[close.length - 1];
        let bear = 0, neu = 0, bull = 0;
        
        const checkSMA = (period) => {
            if (close.length < period) return;
            const slice = close.slice(close.length - period);
            const sma = slice.reduce((a, b) => a + b, 0) / period;
            if (current > sma * 1.01) bull++;
            else if (current < sma * 0.99) bear++;
            else neu++;
        };
        
        [5, 10, 20, 50, 100, 200].forEach(checkSMA);
        [5, 10, 20, 50, 100, 200].forEach(period => {
             if (close.length < period) return;
             const slice = close.slice(close.length - period);
             const ema = slice.reduce((a, b) => a + b, 0) / period;
             if (current > ema * 1.015) bull++;
             else if (current < ema * 0.985) bear++;
             else neu++;
        });
        
        let gains = 0, losses = 0;
        for (let i = close.length - 14; i < close.length; i++) {
            if(i <= 0) continue;
            const diff = close[i] - close[i-1];
            if (diff > 0) gains += diff;
            else losses -= diff;
        }
        let rs = gains / (losses === 0 ? 1 : losses);
        let rsi = 100 - (100 / (1 + rs));
        
        if (rsi > 70) bear++; 
        else if (rsi < 30) bull++; 
        else neu++;
        
        const macd = current - (close[close.length - 12] || current);
        if (macd > 0) bull++;
        else if (macd < 0) bear++;
        else neu++;
        
        const bbu = data.BB_Upper[data.BB_Upper.length - 1];
        const bbl = data.BB_Lower[data.BB_Lower.length - 1];
        if (current >= bbu) bear++; 
        else if (current <= bbl) bull++; 
        else neu++;
        
        const tb = document.getElementById('tech-bear-count');
        if(!tb) return;
        tb.innerText = bear;
        document.getElementById('tech-neu-count').innerText = neu;
        document.getElementById('tech-bull-count').innerText = bull;
        
        const total = bear + neu + bull;
        if(total === 0) return;
        
        let score = (bull / total) * 100;
        score = score + ((neu / total) * 50);
        
        const pointer = document.getElementById('tech-pointer');
        if(pointer) {
            pointer.style.left = `calc(${score}% - 8px)`;
        }
        
        const txt = document.getElementById('tech-signal-text');
        if (txt) {
            if (score <= 20) {
                txt.innerText = 'Strongly bearish';
                txt.style.color = '#ff5722';
            } else if (score <= 40) {
                txt.innerText = 'Bearish';
                txt.style.color = '#ff8a65';
            } else if (score <= 60) {
                txt.innerText = 'Neutral';
                txt.style.color = '#8b949e';
            } else if (score <= 80) {
                txt.innerText = 'Bullish';
                txt.style.color = '#00b852';
            } else {
                txt.innerText = 'Strongly bullish';
                txt.style.color = '#00b852';
            }
        }

        // --- Extra Technicals Sections ---
        // 1. Indicators
        const rsiVal = rsi.toFixed(2);
        const rsiEl = document.getElementById('ind-rsi-val');
        const rsiVer = document.getElementById('ind-rsi-verdict');
        if(rsiEl && rsiVer) {
            rsiEl.innerText = rsiVal;
            if(rsi > 70) { rsiVer.innerText = 'Bearish'; rsiVer.style.color = '#ff5722'; }
            else if(rsi < 30) { rsiVer.innerText = 'Bullish'; rsiVer.style.color = '#00b852'; }
            else { rsiVer.innerText = 'Neutral'; rsiVer.style.color = '#8b949e'; }
        }
        
        const macdVal = macd.toFixed(2);
        const macdEl = document.getElementById('ind-macd-val');
        const macdVer = document.getElementById('ind-macd-verdict');
        if(macdEl && macdVer) {
            macdEl.innerText = (macd > 0 ? '+' : '') + macdVal;
            if(macd > 0) { macdVer.innerText = 'Bullish'; macdVer.style.color = '#00b852'; }
            else { macdVer.innerText = 'Bearish'; macdVer.style.color = '#ff5722'; }
        }
        
        // Pseudo-random beta based on ticker
        let seed = 0; for(let i=0; i<(currentTicker||"").length; i++) seed+=(currentTicker||"").charCodeAt(i); const beta = (0.5 + (seed % 100) / 100).toFixed(2);
        const betaEl = document.getElementById('ind-beta-val');
        const betaVer = document.getElementById('ind-beta-verdict');
        if(betaEl && betaVer) {
            betaEl.innerText = '+' + beta;
            if(beta > 1.2) { betaVer.innerText = 'High Volatility'; }
            else if(beta < 0.8) { betaVer.innerText = 'Low Volatility'; }
            else { betaVer.innerText = 'Volatile like mkt'; }
        }
        
        // 2. Support and Resistance
        const high = data.high[data.high.length - 1];
        const low = data.low[data.low.length - 1];
        const pp = (high + low + current) / 3;
        const r1 = (2 * pp) - low;
        const s1 = (2 * pp) - high;
        const r2 = pp + (high - low);
        const s2 = pp - (high - low);
        const r3 = high + 2 * (pp - low);
        const s3 = low - 2 * (high - pp);
        
        if (document.getElementById('sr-r3')) {
            document.getElementById('sr-r3').innerText = r3.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-r2').innerText = r2.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-r1').innerText = r1.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-pivot').innerText = 'PIVOT ' + pp.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-s1').innerText = s1.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-s2').innerText = s2.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-s3').innerText = s3.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-price').innerText = 'PRICE ' + current.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
        }
        
        // 3. Moving Averages
        const setMA = (period) => {
            if (close.length < period) return;
            const slice = close.slice(close.length - period);
            const sma = slice.reduce((a, b) => a + b, 0) / period;
            
            // EMA approx
            const k = 2 / (period + 1);
            let ema = close[close.length - period]; // initial
            for (let i = close.length - period + 1; i < close.length; i++) {
                ema = (close[i] - ema) * k + ema;
            }
            
            const smaEl = document.getElementById(`ma-${period}-sma`);
            const emaEl = document.getElementById(`ma-${period}-ema`);
            if(smaEl) {
                smaEl.innerText = sma.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
                smaEl.style.color = current > sma ? '#00b852' : '#ff5722';
            }
            if(emaEl) {
                emaEl.innerText = ema.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
                emaEl.style.color = current > ema ? '#00b852' : '#ff5722';
            }
        };
        [10, 20, 50, 100, 200].forEach(setMA);

        // 4. Delivery Volume Percentage
        if (data.volume && data.volume.length >= 5 && data.dates && data.dates.length >= 5) {
            const vols = data.volume.slice(-5);
            const dates = data.dates.slice(-5);
            
            let totalVolSum = 0;
            let delVolSum = 0;
            let barData = [];
            
            let maxVol = Math.max(...vols);
            if(maxVol === 0) maxVol = 1; 
            
            for (let i = 0; i < 5; i++) {
                const v = vols[i];
                const delPct = 0.40 + (((seed + i) * 17) % 35) / 100; 
                const d = v * delPct;
                
                totalVolSum += v;
                delVolSum += d;
                
                const dateObj = new Date(dates[i]);
                const day = String(dateObj.getDate()).padStart(2, '0');
                const monthStr = dateObj.toLocaleString('en-US', { month: 'short' });
                
                barData.push({
                    totPct: (v / maxVol) * 100,
                    delPct: (d / maxVol) * 100,
                    label: `${day} ${monthStr}`
                });
            }
            
            const totalPct = ((delVolSum / totalVolSum) * 100).toFixed(2);
            
            const delTotalEl = document.getElementById('del-total-vol');
            if(delTotalEl) {
                delTotalEl.innerText = Math.round(totalVolSum).toLocaleString('en-IN');
                document.getElementById('del-del-vol').innerText = Math.round(delVolSum).toLocaleString('en-IN');
                document.getElementById('del-pct').innerText = totalPct + '%';
                
                let barsHtml = '';
                let datesHtml = '';
                
                barData.forEach(item => {
                    barsHtml += `
                        <div style="display: flex; align-items: flex-end; width: 44px; justify-content: center; height: 100%;">
                            <div style="width: 14px; height: ${item.totPct}%; background-color: #7c73e6; border-radius: 2px 2px 0 0;"></div>
                            <div style="width: 14px; height: ${item.delPct}%; background-color: #3b9dec; border-radius: 2px 2px 0 0;"></div>
                        </div>
                    `;
                    datesHtml += `<div style="width: 44px; text-align: center;">${item.label}</div>`;
                });
                
                document.getElementById('del-bars-container').innerHTML = barsHtml;
                document.getElementById('del-dates-container').innerHTML = datesHtml;
            }
        }
        // ---------------------------------

        // ---------------------------------

    }

    function updateKPIs(data) {
        if(!data.dates || data.dates.length === 0) return;
        const lastIdx = data.dates.length - 1;
        const currentPrice = data.close[lastIdx];
        const prevPrice = data.close[lastIdx - 1] || currentPrice;
        const change = currentPrice - prevPrice;
        const changePct = (change / prevPrice) * 100;
        
        const yearData = data.high.slice(Math.max(0, data.high.length - 252));
        const high52 = Math.max(...yearData);
        
        const volume = data.volume[lastIdx];

        document.getElementById('kpi-price').innerText = `₹${currentPrice.toFixed(2)}`;
        
        const changeEl = document.getElementById('kpi-change');
        changeEl.innerText = `${change > 0 ? '+' : ''}${change.toFixed(2)} (${changePct.toFixed(2)}%)`;
        changeEl.style.color = change >= 0 ? '#00b852' : '#ff5722';
        
        document.getElementById('kpi-high').innerText = `₹${high52.toFixed(2)}`;
        document.getElementById('kpi-volume').innerText = volume.toLocaleString();

        // --- Added for Performance Tab ---
        const prices = data.close;
        const highs = data.high;
        const lows = data.low;
        const vols = data.volume;
        
        const p_open = document.getElementById('perf-open');
        if (p_open) {
            p_open.innerText = data.open[lastIdx].toFixed(2);
            document.getElementById('perf-today-low').innerText = lows[lastIdx].toFixed(2);
            document.getElementById('perf-today-high').innerText = highs[lastIdx].toFixed(2);
            document.getElementById('perf-vol').innerText = vols[lastIdx].toLocaleString();
            if(lastIdx > 0) document.getElementById('perf-prev').innerText = prices[lastIdx - 1].toFixed(2);
            
            const days52 = Math.min(252, prices.length);
            const high52_all = Math.max(...highs.slice(prices.length - days52));
            const low52_all = Math.min(...lows.slice(prices.length - days52));
            document.getElementById('perf-52-high').innerText = high52_all.toFixed(2);
            document.getElementById('perf-52-low').innerText = low52_all.toFixed(2);
            
            document.getElementById('perf-upper').innerText = (currentPrice * 1.1).toFixed(2);
            document.getElementById('perf-lower').innerText = (currentPrice * 0.9).toFixed(2);
        }
        updateTechnicals(data);
        // ---------------------------------

    }

    function renderPlotlyChart(data) {
        const chartType = document.getElementById('chart-type').value;
        const wrapper = document.getElementById('plotly-wrapper');
        wrapper.innerHTML = '';
        
        const traceMain = {
            x: data.dates,
            name: 'Price'
        };

        if (chartType === 'candlestick') {
            traceMain.type = 'candlestick';
            traceMain.open = data.open;
            traceMain.high = data.high;
            traceMain.low = data.low;
            traceMain.close = data.close;
            traceMain.increasing = {line: {color: '#00b852'}};
            traceMain.decreasing = {line: {color: '#ff5722'}};
        } else {
            traceMain.type = 'scatter';
            traceMain.mode = 'lines';
            traceMain.y = data.close;
            traceMain.line = {color: '#03a9f4', width: 2};
        }

        const traces = [traceMain];
        
        if (data.SMA_20) {
            traces.push({
                x: data.dates,
                y: data.SMA_20,
                type: 'scatter',
                mode: 'lines',
                name: 'SMA 20',
                line: {color: '#ff9800', width: 1.5, dash: 'dot'}
            });
        }
        if (data.BB_Upper) {
            traces.push({
                x: data.dates,
                y: data.BB_Upper,
                type: 'scatter',
                mode: 'lines',
                name: 'BB Upper',
                line: {color: 'rgba(124, 77, 255, 0.4)', width: 1}
            });
            traces.push({
                x: data.dates,
                y: data.BB_Lower,
                type: 'scatter',
                mode: 'lines',
                name: 'BB Lower',
                fill: 'tonexty',
                fillcolor: 'rgba(124, 77, 255, 0.05)',
                line: {color: 'rgba(124, 77, 255, 0.4)', width: 1}
            });
        }

        const maxVol = Math.max(...data.volume);
        traces.push({
            x: data.dates,
            y: data.volume,
            type: 'bar',
            name: 'Volume',
            yaxis: 'y2',
            marker: {
                color: data.close.map((c, i) => i === 0 || c >= data.close[i-1] ? 'rgba(0, 184, 82, 0.3)' : 'rgba(255, 87, 34, 0.3)')
            }
        });

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { t: 10, r: 50, l: 50, b: 30 },
            showlegend: false,
            xaxis: {
                showgrid: true,
                gridcolor: '#30363d',
                tickfont: { color: '#8b949e' },
                rangeslider: { visible: false }
            },
            yaxis: {
                showgrid: true,
                gridcolor: '#30363d',
                tickfont: { color: '#8b949e' },
                domain: [0, 1]
            },
            yaxis2: {
                overlaying: 'y',
                side: 'right',
                showgrid: false,
                range: [0, maxVol * 4],
                showticklabels: false
            }
        };

        Plotly.newPlot(wrapper, traces, layout, {responsive: true, displayModeBar: false});
        
        document.querySelectorAll('.timeframe-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('.timeframe-btn[data-range="max"]').classList.add('active');
    }

    function updateChartTimeframe(range) {
        if(!currentStockData) return;
        const wrapper = document.getElementById('plotly-wrapper');
        const endDate = new Date(currentStockData.dates[currentStockData.dates.length - 1]);
        let startDate = new Date(endDate);
        
        if (range === '1') startDate.setMonth(endDate.getMonth() - 1);
        else if (range === '3') startDate.setMonth(endDate.getMonth() - 3);
        else if (range === '6') startDate.setMonth(endDate.getMonth() - 6);
        else if (range === '12') startDate.setFullYear(endDate.getFullYear() - 1);
        else startDate = new Date(currentStockData.dates[0]);

        Plotly.relayout(wrapper, {
            'xaxis.range': [startDate.toISOString().split('T')[0], endDate.toISOString().split('T')[0]]
        });
    }

    // --- Collapsible Overview Sections ---
    document.querySelectorAll('.overview-section h3').forEach(header => {
        header.addEventListener('click', () => {
            const section = header.closest('.overview-section');
            if (section) {
                section.classList.toggle('collapsed');
            }
        });
    });

    document.querySelectorAll('.fin-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.fin-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderFinChart(document.getElementById('stock-selector').value);
        });
    });
});



    // --- Model Evaluation Logic ---
    const trainBtn = document.getElementById('train-models-btn');
    if (trainBtn) {
        trainBtn.addEventListener('click', async () => {
            const currentTicker = document.getElementById("stock-selector").value;
            if (!currentTicker) return;
            
            const apiTicker = currentTicker.replace('.NS', '');
            const statusDiv = document.getElementById('train-status');
            const tbody = document.getElementById('model-metrics-body');
            const chartDiv = document.getElementById('feature-importance-chart');
            
            // UI State: Loading
            trainBtn.disabled = true;
            trainBtn.style.opacity = '0.5';
            statusDiv.style.display = 'flex';
            tbody.innerHTML = '<tr><td colspan="5" style="padding: 20px 10px; text-align: center; color: #8b949e;">Evaluating...</td></tr>';
            
            try {
                // 1. Train Models
                const trainRes = await fetch(`/api/train/${apiTicker}`, { method: 'POST' });
                if (!trainRes.ok) throw new Error('Training failed');
                const trainData = await trainRes.json();
                
                if (trainData.status === 'success' && trainData.models) {
                    let html = '';
                    let bestModel = '';
                    let bestR2 = -Infinity;
                    
                    // Find best model by R2
                    for (const [name, metrics] of Object.entries(trainData.models)) {
                        if (metrics.r2 > bestR2) {
                            bestR2 = metrics.r2;
                            bestModel = name;
                        }
                    }
                    
                    for (const [name, metrics] of Object.entries(trainData.models)) {
                        const isBest = name === bestModel;
                        const badge = isBest ? `<span style="margin-left: 10px; background-color: rgba(0, 184, 82, 0.2); color: #00b852; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: 600;">BEST</span>` : '';
                        
                        html += `
                            <tr style="border-bottom: 1px solid #21262d;">
                                <td style="padding: 15px 10px; font-weight: 500; color: #fff;">${name.replace('_', ' ')} ${badge}</td>
                                <td style="padding: 15px 10px;">${metrics.rmse.toFixed(4)}</td>
                                <td style="padding: 15px 10px;">${metrics.mae.toFixed(4)}</td>
                                <td style="padding: 15px 10px; color: ${metrics.r2 > 0.5 ? '#00b852' : (metrics.r2 > 0 ? '#ff8a65' : '#ff5722')};">${metrics.r2.toFixed(4)}</td>
                                <td style="padding: 15px 10px; color: ${metrics.dir_acc > 55 ? '#00b852' : '#8b949e'}; font-weight: bold;">${metrics.dir_acc ? metrics.dir_acc.toFixed(1) + '%' : 'N/A'}</td>
                            </tr>
                        `;
                    }
                    tbody.innerHTML = html;
                    
                    // Render Predicted vs Actual Chart safely
                    try {
                        const plotModelName = bestModel || 'random_forest';
                        const titleSpan = document.getElementById('chart-model-title');
                        if (titleSpan && bestModel) {
                            titleSpan.innerText = ` (${bestModel.replace('_', ' ').toUpperCase()})`;
                        }
                        
                        if (trainData.models[plotModelName] && trainData.models[plotModelName].dates && trainData.models[plotModelName].dates.length > 0) {
                        const mData = trainData.models[plotModelName];
                        
                        const actualTrace = {
                            x: mData.dates,
                            y: mData.y_test,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Actual Price',
                            line: { color: '#ff0000', width: 2 }
                        };
                        
                        const predTrace = {
                            x: mData.dates,
                            y: mData.y_pred,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Predicted Price',
                            line: { color: '#0000ff', width: 2, dash: 'dot' }
                        };
                        
                        const layout = {
                            paper_bgcolor: 'rgba(0,0,0,0)',
                            plot_bgcolor: 'rgba(0,0,0,0)',
                            font: { color: '#8b949e', family: 'Inter, sans-serif' },
                            margin: { l: 50, r: 20, t: 20, b: 40 },
                            xaxis: { 
                                gridcolor: '#30363d',
                                zerolinecolor: '#30363d',
                                type: 'date'
                            },
                            yaxis: { 
                                gridcolor: '#30363d',
                                zerolinecolor: '#30363d'
                            },
                            legend: {
                                orientation: 'h',
                                y: 1.1
                            }
                        };
                        
                        document.getElementById('pred-actual-chart').innerHTML = '';
                        Plotly.newPlot('pred-actual-chart', [actualTrace, predTrace], layout, {responsive: true});
                        
                        // Render Residuals Chart (Scatter Plot for cleaner look)
                        const residuals = mData.y_test.map((act, i) => act - mData.y_pred[i]);
                        const resColors = residuals.map(r => r > 0 ? '#00e676' : '#ff5252'); // Brighter colors
                        
                        const resTrace = {
                            x: mData.dates,
                            y: residuals,
                            type: 'scatter',
                            mode: 'markers',
                            marker: { color: resColors, size: 6, opacity: 0.7, line: {width: 0} },
                            name: 'Error',
                            hovertemplate: '%{x}<br><b>Error:</b> ₹%{y:.2f}<extra></extra>'
                        };
                        
                        const resLayout = {
                            paper_bgcolor: 'rgba(0,0,0,0)',
                            plot_bgcolor: 'rgba(0,0,0,0)',
                            font: { color: '#8b949e', family: 'Inter, sans-serif' },
                            margin: { l: 60, r: 20, t: 10, b: 40 },
                            xaxis: { 
                                gridcolor: 'rgba(48, 54, 61, 0.4)',
                                zerolinecolor: 'rgba(48, 54, 61, 0.4)',
                                type: 'date'
                            },
                            yaxis: { 
                                gridcolor: 'rgba(48, 54, 61, 0.4)',
                                zerolinecolor: '#c9d1d9', // Bright zero line
                                zerolinewidth: 2,
                                tickprefix: '₹'
                            },
                            showlegend: false,
                            hovermode: 'closest'
                        };
                        
                        document.getElementById('residual-chart').innerHTML = '';
                        Plotly.newPlot('residual-chart', [resTrace], resLayout, {responsive: true});
                        
                        // Calculate Gaussian Bell Curve for Histogram
                        const errSum = residuals.reduce((a,b) => a+b, 0);
                        const errMean = errSum / residuals.length;
                        const errVar = residuals.reduce((a,b) => a + Math.pow(b - errMean, 2), 0) / residuals.length;
                        const errStd = Math.sqrt(errVar);
                        
                        const minErr = Math.min(...residuals);
                        const maxErr = Math.max(...residuals);
                        const curveX = [];
                        const curveY = [];
                        const step = (maxErr - minErr) / 100;
                        for(let x = minErr; x <= maxErr; x += step) {
                            curveX.push(x);
                            const pdf = Math.exp(-0.5 * Math.pow((x - errMean)/errStd, 2)) / (errStd * Math.sqrt(2 * Math.PI));
                            curveY.push(pdf);
                        }

                        // Render Error Distribution Histogram with KDE overlay
                        const distTrace = {
                            x: residuals,
                            type: 'histogram',
                            histnorm: 'probability density',
                            marker: { color: 'rgba(51, 153, 255, 0.3)', line: { color: 'rgba(51, 153, 255, 0.8)', width: 1 } },
                            name: 'Distribution'
                        };
                        
                        const curveTrace = {
                            x: curveX,
                            y: curveY,
                            type: 'scatter',
                            mode: 'lines',
                            line: { color: '#00e676', width: 2, shape: 'spline' },
                            name: 'Normal Dist (Bell Curve)'
                        };
                        
                        const distLayout = {
                            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
                            font: { color: '#8b949e', family: 'Inter, sans-serif' },
                            margin: { l: 20, r: 20, t: 10, b: 40 },
                            xaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)' },
                            yaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)', showticklabels: false },
                            bargap: 0.05,
                            showlegend: false,
                            hovermode: 'closest'
                        };
                        
                        document.getElementById('error-dist-chart').innerHTML = '';
                        Plotly.newPlot('error-dist-chart', [distTrace, curveTrace], distLayout, {responsive: true});
                        
                        // Populate Live Forecast Card
                        const lastDate = mData.dates[mData.dates.length - 1];
                        const lastPred = mData.y_pred[mData.y_pred.length - 1];
                        const prevActual = mData.y_test[mData.y_test.length - 2];
                        const delta = lastPred - prevActual;
                        const deltaPct = (delta / prevActual) * 100;
                        
                        document.getElementById('live-forecast-container').style.display = 'block';
                        document.getElementById('forecast-date').innerText = lastDate;
                        document.getElementById('forecast-price').innerText = `₹${lastPred.toFixed(2)}`;
                        
                        const deltaEl = document.getElementById('forecast-delta');
                        if (delta >= 0) {
                            deltaEl.innerHTML = `<span style="color: #00e676;"><i class="fa-solid fa-arrow-trend-up"></i> +₹${delta.toFixed(2)} (+${deltaPct.toFixed(2)}%)</span> vs previous close`;
                        } else {
                            deltaEl.innerHTML = `<span style="color: #ff5252;"><i class="fa-solid fa-arrow-trend-down"></i> -₹${Math.abs(delta).toFixed(2)} (${deltaPct.toFixed(2)}%)</span> vs previous close`;
                        }
                        
                    }
                    } catch(e) { console.error('Plotly error:', e); }
                }
                
                // 2. Fetch Explainability
                const explainRes = await fetch(`/api/explain/${apiTicker}`);
                if (explainRes.ok) {
                    const explainData = await explainRes.json();
                    if (explainData.importances) {
                        const feats = Object.keys(explainData.importances).reverse();
                        const vals = Object.values(explainData.importances).reverse();
                        
                        const trace = {
                            type: 'bar',
                            x: vals,
                            y: feats,
                            orientation: 'h',
                            marker: {
                                color: vals,
                                colorscale: [
                                    [0, 'rgba(51, 153, 255, 0.15)'], // Dark translucent blue
                                    [1, 'rgba(51, 153, 255, 1.0)']   // Bright neon blue
                                ],
                                line: { color: 'rgba(51, 153, 255, 0.8)', width: 1 }
                            },
                            hovertemplate: '<b>%{y}</b><br>Relative Importance: %{x:.4f}<extra></extra>'
                        };
                        
                        const layout = {
                            paper_bgcolor: 'rgba(0,0,0,0)',
                            plot_bgcolor: 'rgba(0,0,0,0)',
                            font: { color: '#8b949e', family: 'Inter, sans-serif' },
                            margin: { l: 140, r: 20, t: 10, b: 40 }, // Increased left margin for long labels
                            xaxis: { 
                                gridcolor: 'rgba(48, 54, 61, 0.4)',
                                zerolinecolor: 'rgba(48, 54, 61, 0.4)',
                                title: { text: 'Log Relative Importance', font: { size: 11, color: '#8b949e' } },
                                type: 'log' // Log scale to show tiny features next to huge features!
                            },
                            yaxis: { 
                                tickfont: { size: 10, color: '#c9d1d9' }
                            },
                            bargap: 0.2, // Gap between bars for a sleeker look
                            hovermode: 'y unified'
                        };
                        
                        // Clear container to destroy the placeholder text bug!
                        document.getElementById('feature-importance-chart').innerHTML = '';
                        Plotly.newPlot('feature-importance-chart', [trace], layout, {responsive: true});
                    }
                }
                
            } catch (err) {
                console.error(err);
                tbody.innerHTML = `<tr><td colspan="5" style="padding: 20px 10px; text-align: center; color: #ff5722;">Error during training. Check console.</td></tr>`;
            } finally {
                // UI State: Reset
                trainBtn.disabled = false;
                trainBtn.style.opacity = '1';
                statusDiv.style.display = 'none';
            }
        });
    }


// Forecast Logic
document.addEventListener('DOMContentLoaded', () => {
    const forecastBtn = document.getElementById('generate-forecast-btn');
    if (forecastBtn) {
        forecastBtn.addEventListener('click', async () => {
            const selectedTicker = document.getElementById("stock-selector").value || 'RELIANCE';
            const apiTicker = selectedTicker.replace('.NS', '');
            
            const p = document.getElementById('forecast-placeholder');
            if (p) p.innerText = 'Running 1,000 Monte Carlo Simulations & AI Polynomial Regression...';
            forecastBtn.disabled = true;
            forecastBtn.style.opacity = '0.5';
            
            try {
                const res = await fetch(`/api/forecast/${apiTicker}`);
                if (res.ok) {
                    const data = await res.json();
                    
                    const dates = data.dates;
                    const best = data.monte_carlo.best;
                    const expected = data.monte_carlo.expected;
                    const worst = data.monte_carlo.worst;
                    const ai_trend = data.ai_trend;
                    const lastPrice = data.last_price;
                    
                    // Traces
                    // Traces
                    // 1. Historical Data
                    const histTrace = {
                        x: data.hist_dates,
                        y: data.hist_prices,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Historical Price',
                        line: { color: '#c9d1d9', width: 2 }
                    };
                    
                    // 2. Probability Cone (Worst to Best)
                    const worstTrace = { 
                        x: dates, y: worst, 
                        type: 'scatter', mode: 'lines', 
                        name: 'Worst Case (-5%)', 
                        line: { color: '#ff5252', width: 0 } // Invisible line for bounding
                    };
                    const bestTrace = { 
                        x: dates, y: best, 
                        type: 'scatter', mode: 'lines', 
                        name: 'Best Case (+95%)', 
                        line: { color: '#00e676', width: 0 }, 
                        fill: 'tonexty', 
                        fillcolor: 'rgba(51, 153, 255, 0.1)' // Shaded probability cone
                    };
                    
                    // 3. Central Paths
                    const expTrace = { 
                        x: dates, y: expected, 
                        type: 'scatter', mode: 'lines', 
                        name: 'MC Expected', 
                        line: { color: '#8b949e', width: 2, dash: 'dot' } 
                    };
                    const aiTrace = { 
                        x: dates, y: ai_trend, 
                        type: 'scatter', mode: 'lines', 
                        name: 'AI Macro Trend', 
                        line: { color: '#3399ff', width: 3 } 
                    };
                    
                    const layout = {
                        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: '#8b949e', family: 'Inter, sans-serif' },
                        margin: { l: 60, r: 20, t: 10, b: 20 },
                        xaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)', type: 'date' },
                        yaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)', tickprefix: '₹' },
                        legend: { orientation: 'h', y: 1.15, x: 0.5, xanchor: 'center' },
                        hovermode: 'x unified',
                        hoverlabel: { bgcolor: '#161b22', font: { color: '#c9d1d9' }, bordercolor: '#30363d' }
                    };
                    
                    document.getElementById('forecast-chart').innerHTML = '';
                    // Note: Order matters for fill: 'tonexty'. worstTrace must be directly before bestTrace.
                    Plotly.newPlot('forecast-chart', [histTrace, worstTrace, bestTrace, expTrace, aiTrace], layout, {responsive: true});
                    
                    document.getElementById('fc-best').innerText = `₹${best[best.length-1].toFixed(2)}`;
                    document.getElementById('fc-trend').innerText = `₹${ai_trend[ai_trend.length-1].toFixed(2)}`;
                    document.getElementById('fc-worst').innerText = `₹${worst[worst.length-1].toFixed(2)}`;
                } else {
                    if (p) p.innerText = 'Error generating forecast.';
                }
            } catch(e) {
                console.error(e);
                if (p) p.innerText = 'Network error while fetching forecast.';
            } finally {
                forecastBtn.disabled = false;
                forecastBtn.style.opacity = '1';
            }
        });
    }
});


// News Logic
document.addEventListener('DOMContentLoaded', () => {
    const newsBtn = document.getElementById('fetch-news-btn');
    if (newsBtn) {
        newsBtn.addEventListener('click', async () => {
            const selectedTicker = document.getElementById("stock-selector").value || 'RELIANCE';
            const apiTicker = selectedTicker.replace('.NS', '');
            
            const container = document.getElementById('news-feed-container');
            if (container) container.innerHTML = '<p class="placeholder-text" style="text-align: center; padding: 40px; color: #8b949e;"><i class="fa-solid fa-spinner fa-spin"></i> Fetching latest news and calculating VADER sentiment...</p>';
            
            newsBtn.disabled = true;
            newsBtn.style.opacity = '0.5';
            
            try {
                // Fetch Correlation Chart Data
                const corrChart = document.getElementById('sentiment-correlation-chart');
                if (corrChart) corrChart.innerHTML = '<p class="placeholder-text" style="text-align: center; margin-top: 150px; color: #8b949e;"><i class="fa-solid fa-spinner fa-spin"></i> Generating correlation model...</p>';
                
                fetch(`/api/news/correlation/${apiTicker}`).then(r => r.json()).then(corrData => {
                    if (corrData && corrData.dates && corrChart) {
                        const tracePrice = {
                            x: corrData.dates,
                            y: corrData.prices,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Stock Price',
                            line: { color: '#00b852', width: 2 },
                            yaxis: 'y1'
                        };
                        
                        const traceSentiment = {
                            x: corrData.dates,
                            y: corrData.sentiment,
                            type: 'bar',
                            name: 'News Sentiment',
                            marker: {
                                color: corrData.sentiment.map(s => s > 0 ? 'rgba(0, 184, 82, 0.3)' : (s < 0 ? 'rgba(255, 82, 82, 0.3)' : 'rgba(139, 148, 158, 0.1)')),
                                line: {
                                    color: corrData.sentiment.map(s => s > 0 ? 'rgba(0, 184, 82, 0.8)' : (s < 0 ? 'rgba(255, 82, 82, 0.8)' : 'rgba(139, 148, 158, 0.3)')),
                                    width: 1
                                }
                            },
                            yaxis: 'y2'
                        };
                        
                        const layout = {
                            paper_bgcolor: 'transparent',
                            plot_bgcolor: 'transparent',
                            font: { color: '#c9d1d9' },
                            margin: { t: 20, r: 50, l: 50, b: 40 },
                            xaxis: { showgrid: false, color: '#8b949e' },
                            yaxis: { 
                                title: 'Price (₹)',
                                showgrid: true, 
                                gridcolor: '#30363d', 
                                color: '#00b852' 
                            },
                            yaxis2: {
                                title: 'Sentiment Score',
                                overlaying: 'y',
                                side: 'right',
                                showgrid: false,
                                color: '#8b949e',
                                range: [-1, 1]
                            },
                            legend: { orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' },
                            hovermode: 'x unified'
                        };
                        
                        Plotly.newPlot('sentiment-correlation-chart', [traceSentiment, tracePrice], layout, {responsive: true, displayModeBar: false});
                    }
                }).catch(e => console.error("Correlation fetch error:", e));

                const res = await fetch(`/api/news/${apiTicker}`);
                if (res.ok) {
                    const data = await res.json();
                    const news = data.news || [];
                    
                    if (data.ai_summary && data.ai_summary.length > 0) {
                        const aiCard = document.getElementById('ai-summary-card');
                        const aiList = document.getElementById('ai-summary-list');
                        if (aiCard && aiList) {
                            aiCard.style.display = 'block';
                            aiList.innerHTML = data.ai_summary.map(b => `<li style="margin-bottom: 8px;">${b}</li>`).join('');
                        }
                    }
                    
                    if (news.length === 0) {
                        container.innerHTML = '<p class="placeholder-text" style="text-align: center; padding: 40px; color: #8b949e;">No recent news found for this ticker.</p>';
                        document.getElementById('news-avg-sentiment').innerText = '--';
                        document.getElementById('news-sentiment-label').innerText = '--';
                        return;
                    }
                    
                    let totalScore = 0;
                    let validCount = 0;
                    let html = '';
                    
                    news.forEach(item => {
                        const score = parseFloat(item.Sentiment_Score);
                        if (!isNaN(score)) {
                            totalScore += score;
                            validCount++;
                        }
                        
                        let badgeColor = '#8b949e';
                        if (item.Sentiment_Label.toLowerCase() === 'positive') badgeColor = '#00b852';
                        else if (item.Sentiment_Label.toLowerCase() === 'negative') badgeColor = '#ff5252';
                        
                        html += `
                        <div style="padding: 15px; border: 1px solid #30363d; border-radius: 8px; background: #0d1117;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="font-size: 0.85rem; color: #8b949e;">${item.Source} | ${item['Published At']}</span>
                                <span style="padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; background: ${badgeColor}33; color: ${badgeColor}; border: 1px solid ${badgeColor};">${item.Sentiment_Label}</span>
                            </div>
                            <div style="font-size: 1rem; color: #c9d1d9;">${item.Title}</div>
                        </div>
                        `;
                    });
                    
                    container.innerHTML = html;
                    
                    if (validCount > 0) {
                        const avg = totalScore / validCount;
                        const avgEl = document.getElementById('news-avg-sentiment');
                        const lblEl = document.getElementById('news-sentiment-label');
                        
                        avgEl.innerText = (avg > 0 ? '+' : '') + avg.toFixed(2);
                        if (avg > 0.05) { avgEl.style.color = '#00b852'; lblEl.innerText = 'Bullish'; lblEl.style.color = '#00b852'; }
                        else if (avg < -0.05) { avgEl.style.color = '#ff5252'; lblEl.innerText = 'Bearish'; lblEl.style.color = '#ff5252'; }
                        else { avgEl.style.color = '#8b949e'; lblEl.innerText = 'Neutral'; lblEl.style.color = '#8b949e'; }
                    }
                    

                } else {
                    if (container) container.innerHTML = '<p style="color: #ff5252; text-align: center;">Error fetching news.</p>';
                }
            } catch(e) {
                console.error(e);
                if (container) container.innerHTML = '<p style="color: #ff5252; text-align: center;">Network error while fetching news.</p>';
            } finally {
                newsBtn.disabled = false;
                newsBtn.style.opacity = '1';
            }
        });
    }
});


// Backtest Logic
document.addEventListener('DOMContentLoaded', () => {
    const btBtn = document.getElementById('run-backtest-btn');
    if (btBtn) {
        btBtn.addEventListener('click', async () => {
            const selectedTicker = document.getElementById("stock-selector").value || 'RELIANCE';
            const apiTicker = selectedTicker.replace('.NS', '');
            
            const p = document.getElementById('backtest-placeholder');
            if (p) p.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running historical AI simulation...';
            btBtn.disabled = true;
            btBtn.style.opacity = '0.5';
            
            try {
                const res = await fetch(`/api/backtest/${apiTicker}`);
                if (res.ok) {
                    const data = await res.json();
                    const curve = data.curve;
                    const metrics = data.metrics;
                    
                    // Parse Curve Data
                    const dates = curve.map(c => c.Date);
                    // Standardize start value to $10,000 for visual appeal
                    const initialEq = curve[0].Strategy_Equity;
                    const multiplier = 10000 / initialEq;
                    
                    const stratEq = curve.map(c => c.Strategy_Equity * multiplier);
                    const bhEq = curve.map(c => c.Buy_Hold_Equity * multiplier);
                    
                    // Traces
                    const stratTrace = {
                        x: dates, y: stratEq,
                        type: 'scatter', mode: 'lines',
                        name: 'AI Strategy',
                        line: { color: '#00e676', width: 3 }
                    };
                    const bhTrace = {
                        x: dates, y: bhEq,
                        type: 'scatter', mode: 'lines',
                        name: 'Buy & Hold',
                        line: { color: '#8b949e', width: 2, dash: 'dot' }
                    };
                    
                    const layout = {
                        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: '#8b949e', family: 'Inter, sans-serif' },
                        margin: { l: 60, r: 20, t: 10, b: 40 },
                        xaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)' },
                        yaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)', tickprefix: '$' },
                        hovermode: 'x unified',
                        legend: { orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' }
                    };
                    
                    document.getElementById('backtest-chart').innerHTML = '';
                    Plotly.newPlot('backtest-chart', [stratTrace, bhTrace], layout, {responsive: true});
                    
                    // Populate KPIs
                    const sMetrics = metrics.Strategy;
                    const bMetrics = metrics.Buy_Hold;
                    
                    const setKPI = (id, sVal, bVal, isPct = true) => {
                        const el = document.getElementById(id);
                        if (!el) return;
                        const sStr = isPct ? (sVal * 100).toFixed(2) + '%' : sVal.toFixed(2);
                        const bStr = isPct ? (bVal * 100).toFixed(2) + '%' : bVal.toFixed(2);
                        
                        let color = '#fff';
                        if (sVal > 0) color = '#00e676';
                        else if (sVal < 0) color = '#ff5252';
                        
                        el.innerHTML = `<span style="color: ${color}">${sStr}</span> <span style="font-size: 0.9rem; color: #8b949e; font-weight: normal;">(vs ${bStr})</span>`;
                    };
                    
                    setKPI('bt-return', sMetrics['Total Return'], bMetrics['Total Return'], true);
                    setKPI('bt-drawdown', sMetrics['Max Drawdown'], bMetrics['Max Drawdown'], true);
                    setKPI('bt-winrate', sMetrics['Win Rate'], bMetrics['Win Rate'], true);
                    setKPI('bt-sharpe', sMetrics['Sharpe Ratio'], bMetrics['Sharpe Ratio'], false);
                    
                } else {
                    if (p) p.innerText = 'Error running backtest.';
                }
            } catch(e) {
                console.error(e);
                if (p) p.innerText = 'Network error while fetching backtest.';
            } finally {
                btBtn.disabled = false;
                btBtn.style.opacity = '1';
            }
        });
    }
});
