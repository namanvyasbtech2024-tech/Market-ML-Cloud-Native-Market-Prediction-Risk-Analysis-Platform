from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import traceback

from src.data_preprocessing import load_stock_data, list_nifty50_companies

portfolio_router = APIRouter(prefix="/api/portfolio")

class HoldingItem(BaseModel):
    ticker: str
    weight: float  # e.g., 25.0 for 25%
    shares: Optional[float] = None

class PortfolioAnalysisRequest(BaseModel):
    holdings: List[HoldingItem]
    initial_investment: float = 1000000.0  # Default ₹10,00,000 (10 Lakhs)
    risk_free_rate: float = 0.065  # 6.5% Indian 10-Year G-Sec yield

@portfolio_router.get("/default")
async def get_default_portfolio():
    """Returns default diversified Indian blue-chip portfolio configuration."""
    available = list_nifty50_companies()
    return {
        "initial_investment": 1000000.0,
        "risk_free_rate": 0.065,
        "available_tickers": available,
        "holdings": [
            {"ticker": "RELIANCE", "weight": 30.0, "name": "Reliance Industries"},
            {"ticker": "TCS", "weight": 25.0, "name": "Tata Consultancy Services"},
            {"ticker": "INFY", "weight": 25.0, "name": "Infosys Ltd"},
            {"ticker": "ICICIBANK", "weight": 20.0, "name": "ICICI Bank"}
        ]
    }

@portfolio_router.post("/analyze")
async def analyze_portfolio(req: PortfolioAnalysisRequest):
    """
    Analyzes current portfolio, computes Markowitz Efficient Frontier,
    generates AI rebalancing recommendations (Max Sharpe), and
    simulates 1-Year Net Worth Monte Carlo trajectories.
    """
    try:
        if not req.holdings or len(req.holdings) < 2:
            raise HTTPException(status_code=400, detail="Portfolio must contain at least 2 distinct assets for diversification analysis.")

        tickers = [h.ticker.strip().upper().replace(".NS", "") for h in req.holdings]
        input_weights = np.array([float(h.weight) for h in req.holdings], dtype=float)
        
        if np.sum(input_weights) <= 0:
            raise HTTPException(status_code=400, detail="Total portfolio weight must be greater than 0.")
            
        current_weights = input_weights / np.sum(input_weights)
        num_assets = len(tickers)

        # 1. Fetch Historical Close Prices for all tickers
        prices_dict = {}
        last_prices = {}
        
        for t in tickers:
            try:
                df = load_stock_data(t)
                if df.empty or len(df) < 60:
                    continue
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date').drop_duplicates(subset=['Date']).set_index('Date')
                prices_dict[t] = df['Close']
                last_prices[t] = float(df['Close'].iloc[-1])
            except Exception as e:
                print(f"Error loading {t}: {e}")

        valid_tickers = [t for t in tickers if t in prices_dict]
        if len(valid_tickers) < 2:
            raise HTTPException(status_code=400, detail="Could not load historical data for at least 2 valid stocks.")

        # Re-index weights to valid tickers
        valid_indices = [tickers.index(t) for t in valid_tickers]
        current_weights = current_weights[valid_indices]
        current_weights = current_weights / np.sum(current_weights)
        tickers = valid_tickers
        num_assets = len(tickers)

        # Capital and Discrete Share Validation (Indian NSE/BSE does not support fractional shares)
        min_single_share_price = float(min(last_prices[t] for t in tickers))
        min_basket_capital = float(sum(last_prices[t] for t in tickers))
        cheapest_ticker, cheapest_price = min([(t, last_prices[t]) for t in tickers], key=lambda x: x[1])

        if req.initial_investment < min_single_share_price:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient Capital: ₹{req.initial_investment:,.2f} is too low. In the Indian stock market (NSE), fractional shares cannot be traded. The cheapest stock in your portfolio ({cheapest_ticker}) costs ₹{cheapest_price:,.2f}. To buy at least 1 share of each selected stock, you need a minimum capital of ₹{min_basket_capital:,.2f}."
            )

        price_df = pd.DataFrame({t: prices_dict[t] for t in tickers}).dropna()
        if len(price_df) < 60:
            raise HTTPException(status_code=400, detail="Insufficient overlapping historical price history.")

        # 2. Compute Return & Covariance Matrix (Annualized, 252 trading days)
        daily_returns = price_df.pct_change().dropna()
        annual_returns = np.nan_to_num(daily_returns.mean().values * 252.0, nan=0.0, posinf=0.5, neginf=-0.5)
        cov_matrix = np.nan_to_num(daily_returns.cov().values * 252.0, nan=1e-4, posinf=0.1, neginf=1e-4)

        # Current Portfolio Stats
        current_ret = float(np.dot(current_weights, annual_returns))
        current_vol = float(np.sqrt(np.dot(current_weights.T, np.dot(cov_matrix, current_weights))))
        current_sharpe = float((current_ret - req.risk_free_rate) / max(current_vol, 1e-6))

        # Benchmark calculation (Equal-weighted composite of assets)
        bench_weights = np.ones(num_assets) / num_assets
        bench_daily = (daily_returns @ bench_weights)
        port_daily = (daily_returns @ current_weights)
        
        cov_with_bench = float(np.cov(port_daily, bench_daily)[0, 1])
        var_bench = float(np.var(bench_daily))
        portfolio_beta = float(cov_with_bench / max(var_bench, 1e-6))

        # Compute Pairwise Pearson Correlation Matrix & Concentration Risk AI Insights
        corr_df = daily_returns.corr()
        corr_matrix_list = []
        for i_t in tickers:
            row = [round(float(corr_df.loc[i_t, j_t]), 2) for j_t in tickers]
            corr_matrix_list.append(row)

        correlation_insights = []
        for i in range(len(tickers)):
            for j in range(i + 1, len(tickers)):
                t1 = tickers[i]
                t2 = tickers[j]
                r_val = float(corr_df.loc[t1, t2])
                r_pct = round(r_val * 100, 1)
                if r_val >= 0.70:
                    correlation_insights.append({
                        "type": "warning",
                        "pair": f"{t1} & {t2}",
                        "correlation": round(r_val, 2),
                        "message": f"High Correlation Warning: {t1} and {t2} have a {r_pct:.0f}% correlation. Both tend to move in tandem, increasing concentration risk. Consider swapping one for an asset in an uncorrelated sector (e.g. FMCG, Energy, or Pharma)."
                    })
                elif r_val <= 0.25:
                    correlation_insights.append({
                        "type": "positive",
                        "pair": f"{t1} & {t2}",
                        "correlation": round(r_val, 2),
                        "message": f"Strong Diversification Synergy: {t1} and {t2} have a low correlation ({r_pct:.0f}%), effectively cushioning downside risk."
                    })

        if not any(ins["type"] == "warning" for ins in correlation_insights):
            correlation_insights.insert(0, {
                "type": "positive",
                "pair": "Portfolio Overall",
                "correlation": 0.40,
                "message": "Healthy Diversification: No severe asset overlap detected (all pairs have r < 0.70), providing effective risk reduction under Modern Portfolio Theory."
            })

        # 3. Efficient Frontier Monte Carlo Simulation (Modern Portfolio Theory)
        np.random.seed(42)
        n_sim = 4000
        sim_weights = np.random.dirichlet(np.ones(num_assets), size=n_sim)
        sim_rets = sim_weights @ annual_returns
        
        # Vectorized portfolio volatility
        sim_vols = np.sqrt(np.einsum('ij,jk,ik->i', sim_weights, cov_matrix, sim_weights))
        sim_sharpes = (sim_rets - req.risk_free_rate) / np.maximum(sim_vols, 1e-6)

        # Identify Key Portfolios
        max_sharpe_idx = int(np.argmax(sim_sharpes))
        min_vol_idx = int(np.argmin(sim_vols))

        opt_weights = sim_weights[max_sharpe_idx]
        opt_ret = float(sim_rets[max_sharpe_idx])
        opt_vol = float(sim_vols[max_sharpe_idx])
        opt_sharpe = float(sim_sharpes[max_sharpe_idx])

        min_vol_weights = sim_weights[min_vol_idx]
        min_vol_ret = float(sim_rets[min_vol_idx])
        min_vol_vol = float(sim_vols[min_vol_idx])
        min_vol_sharpe = float(sim_sharpes[min_vol_idx])

        # Downsample frontier scatter points for fast frontend rendering (every 10th point)
        sub_sample_indices = np.arange(0, n_sim, 10)
        frontier_points = []
        for idx in sub_sample_indices:
            frontier_points.append({
                "vol": round(float(sim_vols[idx]) * 100, 2),
                "ret": round(float(sim_rets[idx]) * 100, 2),
                "sharpe": round(float(sim_sharpes[idx]), 3)
            })

        # 4. AI Rebalancing Recommendations (Discrete Whole Shares for Indian Market)
        rebalance_recommendations = []
        total_opt_invested = 0.0
        total_cur_invested = 0.0

        for i, t in enumerate(tickers):
            price_i = float(last_prices[t])
            c_w = float(current_weights[i]) * 100.0
            o_w = float(opt_weights[i]) * 100.0
            delta_pct = o_w - c_w
            delta_inr = (delta_pct / 100.0) * req.initial_investment
            
            # Discrete whole share calculations (No fractional shares in NSE/BSE)
            cur_shares = int(np.floor((req.initial_investment * (c_w / 100.0)) / price_i))
            opt_shares = int(np.floor((req.initial_investment * (o_w / 100.0)) / price_i))
            delta_shares = opt_shares - cur_shares

            cur_invested = cur_shares * price_i
            opt_invested = opt_shares * price_i
            total_cur_invested += cur_invested
            total_opt_invested += opt_invested

            if delta_shares > 0:
                action = f"BUY +{delta_shares} shares"
                action_color = "#00e676"
            elif delta_shares < 0:
                action = f"TRIM {delta_shares} shares"
                action_color = "#ff5252"
            else:
                action = "HOLD"
                action_color = "#3399ff"

            stock_ret = float(annual_returns[i]) * 100.0
            stock_vol = float(np.sqrt(cov_matrix[i, i])) * 100.0
            stock_sharpe = float((annual_returns[i] - req.risk_free_rate) / max(np.sqrt(cov_matrix[i, i]), 1e-6))

            rebalance_recommendations.append({
                "ticker": t,
                "current_weight": round(c_w, 1),
                "optimal_weight": round(o_w, 1),
                "delta_pct": round(delta_pct, 1),
                "delta_inr": round(delta_inr, 2),
                "current_shares": cur_shares,
                "optimal_shares": opt_shares,
                "delta_shares": delta_shares,
                "current_invested": round(cur_invested, 2),
                "optimal_invested": round(opt_invested, 2),
                "action": action,
                "action_color": action_color,
                "current_price": round(price_i, 2),
                "stock_ret": round(stock_ret, 1),
                "stock_vol": round(stock_vol, 1),
                "stock_sharpe": round(stock_sharpe, 2)
            })

        cash_reserve_cur = float(req.initial_investment - total_cur_invested)
        cash_reserve_opt = float(req.initial_investment - total_opt_invested)

        # 4b. Execution Order Sheet Generator (Actionable Trade Sheet)
        buy_orders = []
        sell_orders = []
        hold_orders = []
        total_buy_val = 0.0
        total_sell_val = 0.0

        for rec in rebalance_recommendations:
            t = rec["ticker"]
            d_shares = rec["delta_shares"]
            price_i = rec["current_price"]
            trade_val = abs(d_shares) * price_i
            
            if d_shares > 0:
                buy_orders.append({
                    "ticker": t,
                    "action": "BUY",
                    "shares": d_shares,
                    "price": price_i,
                    "value_inr": round(trade_val, 2),
                    "instruction": f"BUY +{d_shares} shares of {t} @ ₹{price_i:,.2f} (~₹{trade_val:,.2f})",
                    "broker_line": f"BUY {d_shares} {t} CNC MARKET"
                })
                total_buy_val += trade_val
            elif d_shares < 0:
                sell_orders.append({
                    "ticker": t,
                    "action": "SELL",
                    "shares": abs(d_shares),
                    "price": price_i,
                    "value_inr": round(trade_val, 2),
                    "instruction": f"SELL {abs(d_shares)} shares of {t} @ ₹{price_i:,.2f} (~₹{trade_val:,.2f})",
                    "broker_line": f"SELL {abs(d_shares)} {t} CNC MARKET"
                })
                total_sell_val += trade_val
            else:
                hold_orders.append({
                    "ticker": t,
                    "action": "HOLD",
                    "shares": 0,
                    "price": price_i,
                    "value_inr": 0.0,
                    "instruction": f"HOLD position in {t} (Optimal weight already matched)",
                    "broker_line": f"HOLD {t}"
                })

        net_cash_flow = total_sell_val - total_buy_val
        order_sheet = {
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "hold_orders": hold_orders,
            "total_buy_val_inr": round(total_buy_val, 2),
            "total_sell_val_inr": round(total_sell_val, 2),
            "net_cash_flow_inr": round(net_cash_flow, 2),
            "total_trades_count": len(buy_orders) + len(sell_orders),
            "optimal_cash_reserve": round(cash_reserve_opt, 2),
            "raw_broker_text": "\n".join(
                [f"SELL {o['shares']} {o['ticker']} CNC" for o in sell_orders] +
                [f"BUY {o['shares']} {o['ticker']} CNC" for o in buy_orders]
            )
        }

        # 4c. Sector & Industry Exposure Breakdown (Institutional 25% Concentration Limit)
        sector_mapping = {
            "TCS": "IT", "INFY": "IT", "WIPRO": "IT", "HCLTECH": "IT", "TECHM": "IT",
            "ICICIBANK": "FINANCE", "HDFCBANK": "FINANCE", "SBIN": "FINANCE", "AXISBANK": "FINANCE", "KOTAKBANK": "FINANCE", "INDUSINDBK": "FINANCE", "BAJFINANCE": "FINANCE", "BAJAJFINSV": "FINANCE",
            "RELIANCE": "ENERGY", "ONGC": "ENERGY", "IOC": "ENERGY", "BPCL": "ENERGY", "POWERGRID": "ENERGY", "NTPC": "ENERGY", "GAIL": "ENERGY", "COALINDIA": "ENERGY",
            "MARUTI": "AUTO", "TATAMOTORS": "AUTO", "M&M": "AUTO", "MM": "AUTO", "BAJAJ-AUTO": "AUTO", "HEROMOTOCO": "AUTO", "EICHERMOT": "AUTO",
            "SUNPHARMA": "PHARMA", "DRREDDY": "PHARMA", "CIPLA": "PHARMA",
            "HINDUNILVR": "FMCG", "ITC": "FMCG", "NESTLEIND": "FMCG", "BRITANNIA": "FMCG", "TITAN": "FMCG", "ASIANPAINT": "FMCG",
            "TATASTEEL": "METALS", "JSWSTEEL": "METALS", "HINDALCO": "METALS", "VEDL": "METALS", "GRASIM": "METALS", "ULTRACEMCO": "METALS", "SHREECEM": "METALS",
            "LT": "INFRA", "ADANIPORTS": "INFRA", "UPL": "INFRA",
            "BHARTIARTL": "TELECOM", "ZEEL": "TELECOM"
        }

        sector_names = {
            "FINANCE": "Banking & Financials",
            "IT": "IT & Technology",
            "ENERGY": "Energy & Power",
            "AUTO": "Automobile & Components",
            "FMCG": "Consumer Goods (FMCG)",
            "PHARMA": "Pharma & Healthcare",
            "METALS": "Metals & Mining",
            "INFRA": "Infrastructure & Capital Goods",
            "TELECOM": "Telecom & Media",
            "DEFAULT": "Diversified / Other"
        }

        sector_agg = {}
        for i, t in enumerate(tickers):
            sec_code = sector_mapping.get(t, "DEFAULT")
            sec_name = sector_names.get(sec_code, "Diversified / Other")
            if sec_name not in sector_agg:
                sector_agg[sec_name] = {
                    "code": sec_code,
                    "sector": sec_name,
                    "current_weight": 0.0,
                    "optimal_weight": 0.0,
                    "stocks": []
                }
            sector_agg[sec_name]["current_weight"] += float(current_weights[i]) * 100.0
            sector_agg[sec_name]["optimal_weight"] += float(opt_weights[i]) * 100.0
            sector_agg[sec_name]["stocks"].append(t)

        sector_list = []
        sector_insights = []
        for sec_name, sdata in sector_agg.items():
            cur_w = round(sdata["current_weight"], 1)
            opt_w = round(sdata["optimal_weight"], 1)
            delta_w = round(opt_w - cur_w, 1)
            cur_inr = round((cur_w / 100.0) * req.initial_investment, 2)
            opt_inr = round((opt_w / 100.0) * req.initial_investment, 2)
            is_over = cur_w > 25.0
            opt_over = opt_w > 25.0
            excess_pct = round(max(0.0, cur_w - 25.0), 1)

            sector_list.append({
                "sector": sec_name,
                "code": sdata["code"],
                "current_weight": cur_w,
                "optimal_weight": opt_w,
                "delta_weight": delta_w,
                "current_inr": cur_inr,
                "optimal_inr": opt_inr,
                "stocks": sdata["stocks"],
                "is_over_limit": is_over,
                "optimal_over_limit": opt_over,
                "limit_excess_pct": excess_pct
            })

            if is_over:
                if not opt_over:
                    sector_insights.append({
                        "type": "warning_resolved",
                        "sector": sec_name,
                        "message": f"Concentration Risk Mitigated: {sec_name} represents {cur_w}% of your current portfolio, exceeding the 25% institutional ceiling. AI Rebalancing reduces it to {opt_w}%, significantly neutralizing single-industry shock exposure."
                    })
                else:
                    sector_insights.append({
                        "type": "warning",
                        "sector": sec_name,
                        "message": f"High Sector Concentration: {sec_name} represents {cur_w}% of your holdings (institutional guideline: max 25%). Consider diversifying across uncorrelated sectors."
                    })

        if not sector_insights:
            sector_insights.append({
                "type": "positive",
                "sector": "Portfolio Overall",
                "message": "Institutional Limit Compliant: All industry exposures remain safely under the 25.0% single-sector concentration ceiling, maintaining robust risk distribution."
            })

        sector_list.sort(key=lambda s: s["current_weight"], reverse=True)
        sector_exposure = {
            "sectors": sector_list,
            "institutional_limit_pct": 25.0,
            "insights": sector_insights
        }

        # 5. Historical Stress Testing & Black Swan Simulator

        crisis_configs = [
            {
                "id": "covid_2020",
                "name": "2020 COVID Crash",
                "period": "Feb - Mar 2020",
                "benchmark_drop": -38.4,
                "description": "Global pandemic liquidity shock triggering the fastest 30%+ collapse in stock market history.",
                "base_recovery_days": 140,
                "sector_multipliers": {
                    "IT": 0.68, "FINANCE": 1.25, "ENERGY": 1.05, "AUTO": 1.30, "PHARMA": 0.35, "FMCG": 0.55, "METALS": 1.20, "INFRA": 1.15, "DEFAULT": 1.00
                }
            },
            {
                "id": "gfc_2008",
                "name": "2008 Global Financial Crisis",
                "period": "Jan - Oct 2008",
                "benchmark_drop": -55.0,
                "description": "Lehman Brothers bankruptcy and worldwide banking freeze causing extended cyclical recession.",
                "base_recovery_days": 460,
                "sector_multipliers": {
                    "IT": 0.85, "FINANCE": 1.35, "ENERGY": 1.15, "AUTO": 1.20, "PHARMA": 0.55, "FMCG": 0.60, "METALS": 1.40, "INFRA": 1.25, "DEFAULT": 1.05
                }
            },
            {
                "id": "rate_hike_2022",
                "name": "2022 Global Rate Hike & Tech Selloff",
                "period": "Jan - Jun 2022",
                "benchmark_drop": -18.2,
                "description": "Aggressive central bank quantitative tightening and geopolitical commodity spikes compressing PE multiples.",
                "base_recovery_days": 185,
                "sector_multipliers": {
                    "IT": 1.55, "FINANCE": 0.85, "ENERGY": 0.55, "AUTO": 0.95, "PHARMA": 0.80, "FMCG": 0.65, "METALS": 1.10, "INFRA": 0.90, "DEFAULT": 1.00
                }
            },
            {
                "id": "oil_shock",
                "name": "Geopolitical Crude Oil Shock",
                "period": "Simulated Supply Crisis",
                "benchmark_drop": -14.5,
                "description": "Strait of Hormuz escalation sending Brent oil above $115, worsening India trade deficit and rupee pressure.",
                "base_recovery_days": 80,
                "sector_multipliers": {
                    "IT": 0.70, "FINANCE": 1.15, "ENERGY": 0.30, "AUTO": 1.40, "PHARMA": 0.75, "FMCG": 0.90, "METALS": 1.05, "INFRA": 1.10, "DEFAULT": 1.00
                }
            }
        ]

        vol_median = float(np.median(np.sqrt(np.diag(cov_matrix))))
        stress_scenarios_results = []

        for c_cfg in crisis_configs:
            bm_drop = c_cfg["benchmark_drop"]
            sec_mult = c_cfg["sector_multipliers"]
            
            cur_drawdown_pct = 0.0
            opt_drawdown_pct = 0.0
            asset_breakdown = []

            for i, t in enumerate(tickers):
                sec = sector_mapping.get(t, "DEFAULT")
                mult = sec_mult.get(sec, sec_mult.get("DEFAULT", 1.0))
                # Volatility scaling relative to median asset volatility
                asset_vol = float(np.sqrt(cov_matrix[i, i]))
                vol_ratio = max(0.7, min(1.4, asset_vol / max(vol_median, 1e-4)))
                
                stock_shock_pct = bm_drop * mult * vol_ratio
                # Cap shock within physical bounds
                stock_shock_pct = max(-90.0, min(-5.0, stock_shock_pct))

                cur_drawdown_pct += (float(current_weights[i]) * stock_shock_pct)
                opt_drawdown_pct += (float(opt_weights[i]) * stock_shock_pct)

                asset_breakdown.append({
                    "ticker": t,
                    "sector": sec,
                    "shock_pct": round(stock_shock_pct, 1)
                })

            cur_loss_inr = (abs(cur_drawdown_pct) / 100.0) * req.initial_investment
            opt_loss_inr = (abs(opt_drawdown_pct) / 100.0) * req.initial_investment
            capital_saved_inr = cur_loss_inr - opt_loss_inr
            drawdown_improvement_pct = abs(cur_drawdown_pct) - abs(opt_drawdown_pct)

            # Recovery days estimates
            rec_days_cur = int(round(c_cfg["base_recovery_days"] * (abs(cur_drawdown_pct) / abs(bm_drop)) * (1.0 / max(0.5, 1.0 + current_ret))))
            rec_days_opt = int(round(c_cfg["base_recovery_days"] * (abs(opt_drawdown_pct) / abs(bm_drop)) * (1.0 / max(0.5, 1.0 + opt_ret))))

            stress_scenarios_results.append({
                "id": c_cfg["id"],
                "name": c_cfg["name"],
                "period": c_cfg["period"],
                "description": c_cfg["description"],
                "benchmark_drop_pct": bm_drop,
                "current_drawdown_pct": round(cur_drawdown_pct, 1),
                "optimal_drawdown_pct": round(opt_drawdown_pct, 1),
                "drawdown_improvement_pct": round(drawdown_improvement_pct, 1),
                "current_loss_inr": round(cur_loss_inr, 2),
                "optimal_loss_inr": round(opt_loss_inr, 2),
                "capital_saved_inr": round(capital_saved_inr, 2),
                "recovery_days_cur": max(15, rec_days_cur),
                "recovery_days_opt": max(15, rec_days_opt),
                "assets": asset_breakdown
            })

        # Value at Risk (VaR 95%) & Conditional VaR (Expected Shortfall)
        # 1-Day VaR (95% Confidence)
        var_1d_pct_cur = 1.645 * (current_vol / np.sqrt(252.0)) * 100.0
        var_1d_inr_cur = (var_1d_pct_cur / 100.0) * req.initial_investment

        var_1d_pct_opt = 1.645 * (opt_vol / np.sqrt(252.0)) * 100.0
        var_1d_inr_opt = (var_1d_pct_opt / 100.0) * req.initial_investment

        # 1-Month VaR (21 Trading Days, 95% Confidence)
        var_1m_pct_cur = 1.645 * current_vol * np.sqrt(21.0 / 252.0) * 100.0
        var_1m_inr_cur = (var_1m_pct_cur / 100.0) * req.initial_investment

        var_1m_pct_opt = 1.645 * opt_vol * np.sqrt(21.0 / 252.0) * 100.0
        var_1m_inr_opt = (var_1m_pct_opt / 100.0) * req.initial_investment

        # Conditional VaR (CVaR / Expected Shortfall 95%)
        cvar_pct_cur = 2.063 * current_vol * np.sqrt(21.0 / 252.0) * 100.0
        cvar_inr_cur = (cvar_pct_cur / 100.0) * req.initial_investment

        cvar_pct_opt = 2.063 * opt_vol * np.sqrt(21.0 / 252.0) * 100.0
        cvar_inr_opt = (cvar_pct_opt / 100.0) * req.initial_investment

        stress_testing_data = {
            "var_metrics": {
                "current": {
                    "var_1d_pct": round(var_1d_pct_cur, 2),
                    "var_1d_inr": round(var_1d_inr_cur, 2),
                    "var_1m_pct": round(var_1m_pct_cur, 2),
                    "var_1m_inr": round(var_1m_inr_cur, 2),
                    "cvar_pct": round(cvar_pct_cur, 2),
                    "cvar_inr": round(cvar_inr_cur, 2)
                },
                "optimal": {
                    "var_1d_pct": round(var_1d_pct_opt, 2),
                    "var_1d_inr": round(var_1d_inr_opt, 2),
                    "var_1m_pct": round(var_1m_pct_opt, 2),
                    "var_1m_inr": round(var_1m_inr_opt, 2),
                    "cvar_pct": round(cvar_pct_opt, 2),
                    "cvar_inr": round(cvar_inr_opt, 2)
                }
            },
            "scenarios": stress_scenarios_results
        }

        # 6. 1-Year Net Worth Monte Carlo Simulation (252 Trading Days Ahead)
        days_ahead = 252
        num_mc_paths = 1000
        
        # Drift and daily sigma for both current and optimal
        # Current
        c_daily_drift = (current_ret - 0.5 * (current_vol ** 2)) / 252.0
        c_daily_sigma = current_vol / np.sqrt(252.0)
        
        # Optimal
        opt_daily_drift = (opt_ret - 0.5 * (opt_vol ** 2)) / 252.0
        opt_daily_sigma = opt_vol / np.sqrt(252.0)

        # Standard normal random matrix
        np.random.seed(101)
        Z = np.random.standard_normal((days_ahead, num_mc_paths))
        
        # Cumulative returns
        c_daily_shocks = np.exp(c_daily_drift + c_daily_sigma * Z)
        opt_daily_shocks = np.exp(opt_daily_drift + opt_daily_sigma * Z)

        c_paths = np.zeros((days_ahead, num_mc_paths))
        opt_paths = np.zeros((days_ahead, num_mc_paths))
        
        c_paths[0] = req.initial_investment
        opt_paths[0] = req.initial_investment
        
        for d in range(1, days_ahead):
            c_paths[d] = c_paths[d - 1] * c_daily_shocks[d]
            opt_paths[d] = opt_paths[d - 1] * opt_daily_shocks[d]

        # Extract percentiles over time
        future_dates = pd.bdate_range(start=datetime.now() + timedelta(days=1), periods=days_ahead)
        future_dates_str = [d.strftime('%Y-%m-%d') for d in future_dates]

        c_mc_expected = np.median(c_paths, axis=1)
        c_mc_worst = np.percentile(c_paths, 5, axis=1)
        c_mc_best = np.percentile(c_paths, 95, axis=1)

        opt_mc_expected = np.median(opt_paths, axis=1)
        opt_mc_q25 = np.percentile(opt_paths, 25, axis=1)
        opt_mc_q75 = np.percentile(opt_paths, 75, axis=1)
        opt_mc_worst = np.percentile(opt_paths, 5, axis=1)
        opt_mc_best = np.percentile(opt_paths, 95, axis=1)

        projected_alpha_inr = float(opt_mc_expected[-1] - c_mc_expected[-1])
        alpha_pct = float((projected_alpha_inr / req.initial_investment) * 100.0)

        # 7. Historical Backtest of Rebalanced Portfolio (Equity Curve over 1-3 years)
        backtest_window = min(756, len(price_df))
        bt_price_df = price_df.iloc[-backtest_window:]
        bt_daily_returns = bt_price_df.pct_change().dropna()
        
        bt_dates = [d.strftime('%Y-%m-%d') for d in bt_daily_returns.index]
        
        # Portfolio daily returns
        bt_cur_daily = np.dot(bt_daily_returns.values, current_weights)
        bt_opt_daily = np.dot(bt_daily_returns.values, opt_weights)
        bt_bench_daily = np.dot(bt_daily_returns.values, np.ones(num_assets) / num_assets)

        # Build equity curves starting from initial_investment
        v_base = float(req.initial_investment)
        cur_equity = [v_base]
        opt_equity = [v_base]
        bench_equity = [v_base]

        for r_c, r_o, r_b in zip(bt_cur_daily, bt_opt_daily, bt_bench_daily):
            cur_equity.append(cur_equity[-1] * (1.0 + float(r_c)))
            opt_equity.append(opt_equity[-1] * (1.0 + float(r_o)))
            bench_equity.append(bench_equity[-1] * (1.0 + float(r_b)))

        # Prepend start date (the trading day prior to the first return)
        start_date_str = (bt_daily_returns.index[0] - timedelta(days=1)).strftime('%Y-%m-%d')
        all_bt_dates = [start_date_str] + bt_dates

        def compute_series_metrics(eq_series, daily_rets):
            arr = np.array(eq_series)
            cum_ret = ((arr[-1] - arr[0]) / arr[0]) * 100.0
            num_trading_days = len(daily_rets)
            yrs = max(0.1, num_trading_days / 252.0)
            cagr = (((arr[-1] / arr[0]) ** (1.0 / yrs)) - 1.0) * 100.0 if arr[-1] > 0 else -100.0
            
            peaks = np.maximum.accumulate(arr)
            dds = (arr - peaks) / np.maximum(peaks, 1e-4)
            max_dd = float(np.min(dds)) * 100.0
            
            ann_vol = float(np.std(daily_rets) * np.sqrt(252.0)) * 100.0
            sharpe = (cagr / 100.0 - req.risk_free_rate) / max(ann_vol / 100.0, 1e-4)
            
            return {
                "cum_return_pct": round(cum_ret, 1),
                "cagr_pct": round(cagr, 1),
                "max_drawdown_pct": round(max_dd, 1),
                "volatility_pct": round(ann_vol, 1),
                "sharpe_ratio": round(sharpe, 2),
                "end_value_inr": round(float(arr[-1]), 2)
            }

        cur_metrics = compute_series_metrics(cur_equity, bt_cur_daily)
        opt_metrics = compute_series_metrics(opt_equity, bt_opt_daily)
        bench_metrics = compute_series_metrics(bench_equity, bt_bench_daily)

        historical_alpha_inr = opt_metrics["end_value_inr"] - cur_metrics["end_value_inr"]
        historical_alpha_pct = opt_metrics["cum_return_pct"] - cur_metrics["cum_return_pct"]
        dd_cushion_pct = abs(cur_metrics["max_drawdown_pct"]) - abs(opt_metrics["max_drawdown_pct"])

        step = 1
        if len(all_bt_dates) > 360:
            step = 2

        historical_backtest = {
            "dates": all_bt_dates[::step],
            "current_equity": [round(v, 2) for v in cur_equity[::step]],
            "optimal_equity": [round(v, 2) for v in opt_equity[::step]],
            "benchmark_equity": [round(v, 2) for v in bench_equity[::step]],
            "metrics": {
                "current": cur_metrics,
                "optimal": opt_metrics,
                "benchmark": bench_metrics,
                "alpha_inr": round(historical_alpha_inr, 2),
                "alpha_pct": round(historical_alpha_pct, 1),
                "drawdown_cushion_pct": round(dd_cushion_pct, 1)
            },
            "trading_days": len(bt_daily_returns)
        }

        return {
            "status": "success",
            "initial_investment": req.initial_investment,
            "metrics": {
                "current": {
                    "expected_return_pct": round(current_ret * 100, 2),
                    "volatility_pct": round(current_vol * 100, 2),
                    "sharpe_ratio": round(current_sharpe, 2),
                    "beta": round(portfolio_beta, 2),
                    "expected_end_value": round(float(c_mc_expected[-1]), 2),
                    "worst_case_end_value": round(float(c_mc_worst[-1]), 2),
                    "best_case_end_value": round(float(c_mc_best[-1]), 2)
                },
                "optimal": {
                    "expected_return_pct": round(opt_ret * 100, 2),
                    "volatility_pct": round(opt_vol * 100, 2),
                    "sharpe_ratio": round(opt_sharpe, 2),
                    "expected_end_value": round(float(opt_mc_expected[-1]), 2),
                    "worst_case_end_value": round(float(opt_mc_worst[-1]), 2),
                    "best_case_end_value": round(float(opt_mc_best[-1]), 2),
                    "projected_alpha_inr": round(projected_alpha_inr, 2),
                    "alpha_pct": round(alpha_pct, 2)
                },
                "min_volatility": {
                    "expected_return_pct": round(min_vol_ret * 100, 2),
                    "volatility_pct": round(min_vol_vol * 100, 2),
                    "sharpe_ratio": round(min_vol_sharpe, 2)
                }
            },
            "efficient_frontier": {
                "cloud": frontier_points,
                "current_point": {
                    "vol": round(current_vol * 100, 2),
                    "ret": round(current_ret * 100, 2),
                    "sharpe": round(current_sharpe, 2)
                },
                "optimal_point": {
                    "vol": round(opt_vol * 100, 2),
                    "ret": round(opt_ret * 100, 2),
                    "sharpe": round(opt_sharpe, 2),
                    "weights": {t: round(float(opt_weights[i]) * 100, 1) for i, t in enumerate(tickers)}
                },
                "min_vol_point": {
                    "vol": round(min_vol_vol * 100, 2),
                    "ret": round(min_vol_ret * 100, 2),
                    "sharpe": round(min_vol_sharpe, 2),
                    "weights": {t: round(float(min_vol_weights[i]) * 100, 1) for i, t in enumerate(tickers)}
                }
            },
            "rebalance_recommendations": rebalance_recommendations,
            "order_sheet": order_sheet,
            "sector_exposure": sector_exposure,
            "historical_backtest": historical_backtest,
            "correlation": {
                "tickers": tickers,
                "matrix": corr_matrix_list,
                "insights": correlation_insights
            },
            "discrete_execution": {
                "min_basket_capital": round(min_basket_capital, 2),
                "min_single_share_price": round(min_single_share_price, 2),
                "cheapest_stock": cheapest_ticker,
                "current_invested": round(total_cur_invested, 2),
                "current_cash_reserve": round(cash_reserve_cur, 2),
                "optimal_invested": round(total_opt_invested, 2),
                "optimal_cash_reserve": round(cash_reserve_opt, 2)
            },
            "stress_testing": stress_testing_data,
            "net_worth_simulation": {
                "dates": future_dates_str,
                "current": {
                    "expected": [round(float(v), 2) for v in c_mc_expected],
                    "worst": [round(float(v), 2) for v in c_mc_worst],
                    "best": [round(float(v), 2) for v in c_mc_best]
                },
                "optimal": {
                    "expected": [round(float(v), 2) for v in opt_mc_expected],
                    "q25": [round(float(v), 2) for v in opt_mc_q25],
                    "q75": [round(float(v), 2) for v in opt_mc_q75],
                    "worst": [round(float(v), 2) for v in opt_mc_worst],
                    "best": [round(float(v), 2) for v in opt_mc_best]
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
