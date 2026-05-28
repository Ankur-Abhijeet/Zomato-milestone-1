import os
import sys

# Ensure the backend modules can be imported
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Phase 6/backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import streamlit as st
import asyncio
import os

# Sync Streamlit secrets to environment variables for Pydantic Settings
if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# Import core services from Phase 6 backend
from config.settings import get_settings
from data.repository import RestaurantRepository
from input.validator import validate_preferences
from services.integration import IntegrationService
from services.recommendation_engine import RecommendationEngine

# --- Configuration & Initialization ---
st.set_page_config(
    page_title="Zomato AI Recommendations",
    page_icon="🍽️",
    layout="wide"
)

@st.cache_resource
def load_system():
    """Load settings and repository once per server start."""
    # Bust the lru_cache so it picks up the newly injected environment variable
    get_settings.cache_clear()
    settings = get_settings()
    repo = RestaurantRepository(settings)
    repo.load()
    
    from collections import Counter
    
    # 7 Macro Regions for Bangalore, plus Rest of India
    MACRO_REGIONS = {
        "Bangalore - Central (MG Road, Brigade, etc.)": ["mg road", "brigade", "church", "lavelle", "residency", "shivajinagar", "central", "richmond"],
        "Bangalore - South (Jayanagar, JP Nagar, etc.)": ["jayanagar", "jp nagar", "banashankari", "basavanagudi", "bannerghatta", "kumaraswamy"],
        "Bangalore - South-East (Koramangala, BTM, HSR)": ["koramangala", "btm", "hsr", "madiwala", "bommanahalli"],
        "Bangalore - East (Indiranagar, Old Airport)": ["indiranagar", "old airport", "domlur", "cv raman", "hal"],
        "Bangalore - Tech Corridors (Whitefield, Marathahalli, Bellandur)": ["whitefield", "marathahalli", "bellandur", "sarjapur", "brookefield", "kr puram", "mahadevapura"],
        "Bangalore - North (Kalyan Nagar, Kammanahalli, etc.)": ["kalyan nagar", "kammanahalli", "frazer town", "rt nagar", "hebbal", "yelahanka", "sanjay nagar"],
        "Bangalore - West (Malleshwaram, Rajajinagar, etc.)": ["malleshwaram", "rajajinagar", "yeshwanthpur", "basaveshwara", "vijay nagar", "nagarbhavi"],
        "Bangalore - South Outer (Electronic City)": ["electronic city", "e-city"],
        "Delhi NCR (Delhi, Gurgaon, Noida)": ["delhi", "gurgaon", "noida", "ncr"],
        "Mumbai Metropolitan Region": ["mumbai", "bombay", "bandra", "andheri"],
        "Rest of India (Chennai, Hyderabad, Pune)": ["chennai", "hyderabad", "pune", "kolkata"]
    }

    def assign_macro_region(restaurant):
        # We check the clean Zomato 'listed_in_city' or fallback to area/city
        search_text = (restaurant.extras.get("listed_in_city") or restaurant.area or restaurant.city or "").lower()
        for region_name, keywords in MACRO_REGIONS.items():
            if any(k in search_text for k in keywords):
                return region_name
        return "Bangalore - Other"
        
    # Pre-calculate counts for each macro region
    location_counts = Counter()
    for r in repo.all():
        location_counts[assign_macro_region(r)] += 1
        
    # Ensure we only show regions that actually have restaurants
    unique_locations = [region for region in MACRO_REGIONS.keys() if location_counts.get(region, 0) > 0]
    
    if location_counts.get("Bangalore - Other", 0) > 0:
        unique_locations.append("Bangalore - Other")
    
    # Monkey-patch matches_location so the backend understands our macro-regions
    from data import matching
    if not hasattr(matching, "_original_matches_location"):
        matching._original_matches_location = matching.matches_location
        
        def custom_matches_location(restaurant, query):
            if query in MACRO_REGIONS or query == "Bangalore - Other":
                return assign_macro_region(restaurant) == query
            return matching._original_matches_location(restaurant, query)
            
        matching.matches_location = custom_matches_location
    
    return settings, repo, unique_locations, location_counts

try:
    settings, repo, available_locations, location_counts = load_system()
except Exception as e:
    st.error(f"Failed to load dataset: {e}")
    st.stop()

# --- Sidebar: User Preferences ---
st.sidebar.title("Find Your Perfect Meal")
st.sidebar.markdown("Tell us what you're craving.")

# Default to a popular area if available, else the first option
default_idx = available_locations.index("Bangalore - South-East (Koramangala, BTM, HSR)") if "Bangalore - South-East (Koramangala, BTM, HSR)" in available_locations else 0

location = st.sidebar.selectbox(
    "Location / Region*", 
    options=available_locations, 
    index=default_idx,
    format_func=lambda x: f"{x} ({location_counts[x]} restaurants)"
)

# Peek at the current slider value from session state to calculate the real-time count
current_budget = st.session_state.get("budget_slider", (500, 2000))
min_b, max_b = current_budget

# Calculate how many restaurants match BOTH the selected location and this budget
from data import matching
matching_count = sum(
    1 for r in repo.all() 
    if r.cost_inr is not None 
    and min_b <= r.cost_inr <= max_b
    and matching.matches_location(r, location)
)

budget_range = st.sidebar.slider(
    f"Price Range for Two (₹) ({matching_count} available)", 
    min_value=150, 
    max_value=3000, 
    value=(500, 2000), 
    step=50,
    key="budget_slider"
)
min_budget, max_budget = budget_range

# Simple comma-separated cuisines for Streamlit
cuisines_input = st.sidebar.text_input("Cuisines (comma separated)", value="")

min_rating = st.sidebar.slider("Minimum Rating", min_value=1.0, max_value=5.0, value=3.0, step=0.1)

additional = st.sidebar.text_area("Specific Cravings or Needs", value="", placeholder="e.g., family friendly, open late")

submitted = st.sidebar.button("Get Recommendations")

# --- Main Area ---
st.title("Zomato AI Picks 🍽️")
st.markdown("Powered by Groq LLM · 51,717+ restaurants ready")

if submitted:
    if not location.strip():
        st.error("Please provide a location.")
    else:
        with st.spinner("Analyzing preferences and searching restaurants..."):
            cuisines = [c.strip() for c in cuisines_input.split(",") if c.strip()]
            
            try:
                # Inject the strict budget bounds into the LLM's additional context
                context_budget = f"Budget is strictly ₹{min_budget} to ₹{max_budget} for two."
                enhanced_additional = f"{additional} | {context_budget}" if additional.strip() else context_budget

                # 1. Validate Preferences (pass dummy 'medium' to satisfy Pydantic)
                prefs = validate_preferences({
                    "location": location,
                    "budget": "medium",
                    "cuisines": cuisines,
                    "min_rating": min_rating,
                    "additional": enhanced_additional,
                })
                
                # Monkey-patch the hard filter to use our custom min/max budget range
                from services.filter import HardConstraintFilter
                from models.integration import FilterStepCounts, FilterResult
                from data.matching import matches_location, cuisines_overlap
                
                def custom_filter(self, restaurants, preferences):
                    counts = FilterStepCounts(initial=len(restaurants))
                    results = list(restaurants)

                    results = [r for r in results if matches_location(r, preferences.location)]
                    counts.after_location = len(results)

                    results = [r for r in results if r.rating is not None and r.rating >= preferences.min_rating]
                    counts.after_rating = len(results)

                    # Custom exact cost filtering!
                    results = [r for r in results if r.cost_inr is not None and min_budget <= r.cost_inr <= max_budget]
                    counts.after_budget = len(results)

                    cuisine_filter = preferences.cuisines_for_filter()
                    if cuisine_filter:
                        results = [r for r in results if cuisines_overlap(r.cuisines, cuisine_filter)]
                    counts.after_cuisine = len(results)

                    return FilterResult(candidates=results, step_counts=counts, preferences=preferences)
                
                HardConstraintFilter.filter = custom_filter
                
                # 2. Integration Layer (Filter & Cap)
                integration_service = IntegrationService(repo, settings)
                # Ask LLM for top 10 so we have plenty of backups to replace duplicates
                integration = integration_service.run(prefs, top_k=10)
                
                # Show filter stats
                stats = integration.filter_result.step_counts
                st.caption(f"Filtered {stats.initial} -> {stats.after_location} (Location) -> {stats.after_rating} (Rating) -> {stats.after_budget} (Budget) -> {stats.after_cuisine} (Cuisine)")
                
                if integration.skip_llm:
                    st.warning(integration.user_message or "No restaurants match your filters.")
                else:
                    # 3. Recommendation Engine (LLM)
                    engine = RecommendationEngine(settings)
                    
                    # We run the synchronous LLM wrapper (which usually uses async/threads in FastAPI).
                    # Streamlit handles synchronous code fine, but if we need async:
                    result = asyncio.run(asyncio.to_thread(engine.recommend, integration, prefs))
                    
                    if result.used_fallback:
                        st.warning("⚠️ AI service unavailable. Showing standard top-rated results.")
                    
                    if result.summary:
                        st.info(result.summary)
                    
                    # Deduplicate by name and cap at exactly 5 distinct brands
                    seen = set()
                    deduped_recommendations = []
                    duplicates_skipped = 0
                    
                    for r in result.recommendations:
                        key = r.name.casefold().strip()
                        if key not in seen:
                            seen.add(key)
                            deduped_recommendations.append(r)
                            if len(deduped_recommendations) == 5:
                                break
                        else:
                            duplicates_skipped += 1
                            
                    if duplicates_skipped > 0:
                        st.caption(f"💡 Replaced {duplicates_skipped} duplicate branches to ensure you get 5 distinct options.")
                    
                    # Display the recommendation cards
                    for i, r in enumerate(deduped_recommendations, start=1):
                        with st.container():
                            st.markdown(f"### {i}. {r.name}")
                            st.markdown(f"**Cuisine:** {r.cuisine} | **Rating:** ⭐ {r.rating} | **Cost:** ₹{r.estimated_cost}")
                            st.markdown(f"*{r.explanation}*")
                            st.divider()

            except Exception as e:
                st.error(f"Error during recommendation: {e}")
else:
    st.info("👈 Enter your preferences in the sidebar to get started!")
