from portfolio_manager import load_portfolio
from market.market_data import get_current_price


# ==========================================================
# HEALTH SCORE
# ==========================================================

def calculate_health_score(total_return, largest_weight, holdings):

    score = 100

    # Concentration
    if largest_weight > 0.50:
        score -= 30
    elif largest_weight > 0.40:
        score -= 20
    elif largest_weight > 0.25:
        score -= 10

    # Diversification
    if holdings < 5:
        score -= 15
    elif holdings < 8:
        score -= 5

    # Performance bonus
    if total_return > 20:
        score += 5
    elif total_return < 0:
        score -= 10

    score = max(0, min(100, score))
    return score


# ==========================================================
# RISK LEVEL
# ==========================================================

def determine_risk_level(weight):

    if weight >= 0.50:
        return "Very High"

    elif weight >= 0.35:
        return "High"

    elif weight >= 0.20:
        return "Moderate"

    return "Low"


# ==========================================================
# STAR RATING
# ==========================================================

def determine_stars(score):

    if score >= 90:
        return "★★★★★"

    elif score >= 75:
        return "★★★★☆"

    elif score >= 60:
        return "★★★☆☆"

    elif score >= 40:
        return "★★☆☆☆"

    return "★☆☆☆☆"


# ==========================================================
# CALCULATE EVERYTHING
# ==========================================================

def get_portfolio_analysis():

    portfolio = load_portfolio()

    total_value = 0
    total_cost = 0

    positions = []

    for ticker, info in portfolio.items():

        shares = info["shares"]
        cost_basis = info["cost_basis"]

        current_price = get_current_price(ticker)

        if current_price is None:
            continue

        market_value = shares * current_price
        original_cost = shares * cost_basis

        gain = market_value - original_cost

        if original_cost > 0:
            percent = (gain / original_cost) * 100
        else:
            percent = 0

        total_value += market_value
        total_cost += original_cost

        positions.append(
            {
                "ticker": ticker,
                "shares": shares,
                "value": market_value,
                "gain": gain,
                "percent": percent,
            }
        )

    if len(positions) == 0:
        return None

    total_gain = total_value - total_cost
    total_percent = (total_gain / total_cost) * 100 if total_cost else 0

    largest = max(positions, key=lambda x: x["value"])
    best = max(positions, key=lambda x: x["percent"])
    worst = min(positions, key=lambda x: x["percent"])

    largest_weight = largest["value"] / total_value

    allocations = []

    for p in sorted(positions, key=lambda x: x["value"], reverse=True):

        allocation = (p["value"] / total_value) * 100

        allocations.append(
            {
                "ticker": p["ticker"],
                "allocation": allocation,
            }
        )

    health_score = calculate_health_score(
        total_percent,
        largest_weight,
        len(portfolio),
    )

    risk = determine_risk_level(largest_weight)

    stars = determine_stars(health_score)

    recommendations = []

    if largest_weight > 0.40:
        recommendations.append(
            f"{largest['ticker']} makes up over 40% of your portfolio."
        )
        recommendations.append(
            "Consider reducing concentration or adding new positions."
        )

    elif largest_weight > 0.25:
        recommendations.append(
            f"{largest['ticker']} is your dominant holding."
        )

    if len(portfolio) < 5:
        recommendations.append(
            "Increase diversification by adding more companies or ETFs."
        )

    if total_percent > 20:
        recommendations.append(
            "Excellent long-term performance. Continue investing consistently."
        )

    elif total_percent > 10:
        recommendations.append(
            "Portfolio performance is strong."
        )

    elif total_percent > 0:
        recommendations.append(
            "Portfolio is profitable but has room for improvement."
        )

    else:
        recommendations.append(
            "Portfolio is currently negative. Stay focused on the long term."
        )

    return {
        "portfolio_value": total_value,
        "portfolio_cost": total_cost,
        "portfolio_gain": total_gain,
        "portfolio_return": total_percent,
        "largest": largest,
        "best": best,
        "worst": worst,
        "risk": risk,
        "health": health_score,
        "stars": stars,
        "positions": positions,
        "allocations": allocations,
        "recommendations": recommendations,
    }


# ==========================================================
# DISPLAY
# ==========================================================

def analyze_portfolio():

    analysis = get_portfolio_analysis()

    if analysis is None:
        print("Unable to analyze portfolio.")
        return

    print()
    print("=" * 70)
    print("                     HELIX AI ANALYSIS")
    print("=" * 70)

    print(f"\nPortfolio Value : ${analysis['portfolio_value']:,.2f}")
    print(f"Total Gain      : ${analysis['portfolio_gain']:,.2f}")
    print(f"Overall Return  : {analysis['portfolio_return']:.2f}%")
    print(f"Health Score    : {analysis['health']}/100")
    print(f"Risk Level      : {analysis['risk']}")
    print(f"Rating          : {analysis['stars']}")

    print("\nLargest Holding")
    print("-" * 40)
    print(
        f"{analysis['largest']['ticker']} "
        f"(${analysis['largest']['value']:,.2f})"
    )

    print("\nBest Performer")
    print("-" * 40)
    print(
        f"{analysis['best']['ticker']} "
        f"{analysis['best']['percent']:.2f}%"
    )

    print("\nWorst Performer")
    print("-" * 40)
    print(
        f"{analysis['worst']['ticker']} "
        f"{analysis['worst']['percent']:.2f}%"
    )

    print("\nPortfolio Allocation")
    print("-" * 40)

    for stock in analysis["allocations"]:
        print(f"{stock['ticker']:<8}{stock['allocation']:.2f}%")

    print("\nAI Insights")
    print("-" * 40)

    for insight in analysis["recommendations"]:
        print(f"• {insight}")

    print()
    print("=" * 70)
