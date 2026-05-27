# Stitch UI Generation Spec & Deployment Prompt: Zomato Dark Theme SPA

Use this document as a **High-Fidelity Input Prompt** for AI UI Generators (such as Stitch, v0, or Bolt) to generate the exact webpage look, aesthetic, interactions, and responsive components of the Zomato-inspired dark theme application. 

Additionally, it contains standard **Node.js Express Deployment Specs** to host and serve the React Single Page Application (SPA) inside the production environment.

---

## 🚀 PART 1: STITCH WEB UI GENERATION PROMPT
*(Paste the block below directly into your UI generation tool to output the exact webpage look)*

```text
 A single column stack with the options form nested on top, folding into cards gracefully.
- Top Header: Elegant hero branding containing a "🍽️ Find Your Restaurant" text and subline: "Tell us what you're looking for — our AI will do the rest."

### 3. INTERACTIVE SEARCH FORM (PreferenceForm.tsx)
- Location Input: High-contrast input field with red asterisk (*) for required state. Contains placeholders and alert warning tags underneath.
- Budget SelectioCreate a premium, modern, responsive Zomato-inspired dark-mode React web application for an AI-Powered Restaurant Recommendation System. Follow these strict visual tokens, components, and layout structures to produce the exact UI look:

### 1. DESIGN SYSTEM & DESIGN TOKENS (Dark Glassmorphism)
- Font Family: 'Inter', system-ui, sans-serif (imported from Google Fonts).
- Primary Background: Near-black (#0a0a0a) with sleek smooth scrollbars.
- Surface Cards Backdrop: Charcoal glassmorphism background (rgba(28, 28, 28, 0.7)) with blur filter (backdrop-filter: blur(12px)) and a subtle boundary border (rgba(255, 255, 255, 0.06)).
- Accent Color: Vibrant Zomato Red (#e23744) with hover transition (#c9202e).
- Secondary Text: Warm muted grey (#b0b0b0) for readable sub-headings.
- Animations: Staggered entrance animations (fadeIn translateY 12px) for lists, pulsing skeleton shimmers, and micro-hover transitions (scale lifts by translateY(-4px)).

### 2. PAGE LAYOUT (Home.tsx)
- The layout is a modern single-page dashboard.
- Desktop view: A two-column grid. Left side has a sticky form for selecting restaurant options. Right side has the scrolling results column.
- Mobile view:n Group: 3 large horizontal pill buttons:
  * "💸 Low" (displays label and description: "≤ ₹500" inline).
  * "💳 Medium" (marked active by default using Zomato Red outline glow).
  * "💎 High" (displays label and description: "> ₹1,500").
- Cuisine Chip Manager: Search bar where pressing "Enter" or "," adds custom keywords as tag chips (e.g. "Italian", "Continental"). Tags contain a distinct round "×" delete button that changes state on hover.
- Minimum Rating Slider: A range slider (0.0 to 5.0 in 0.5 steps) decorated with an active Zomato Red gradient track, and a live text badge indicating the stars (e.g. "⭐ 4.5").
- Top-K stepper: Custom adjustment buttons ("−" and "+") with a live digital count display centered.
- Submit Button: A wide button that elevates slightly on hover. If loading is triggered, it replaces text with a spinning loader and shows "Finding your perfect spots...".

### 4. RECOMMENDATIONS LAYOUT (ResultsView.tsx & RestaurantCard.tsx)
- Summary Banner: A beautiful green or Zomato red panel with a "✨" icon summarizing choices dynamically.
- Filter Statistics Pipeline Strip: Renders a horizontal flowing arrow path displaying matching stats at each step:
  * "Total: 50,000" → "Location: 2,000" → "Rating: 1,000" → "Budget: 500" → "Cuisine: 10" → "Sent to AI: 10".
  * Render a distinct "🔁 N duplicate(s) hidden" amber badge when duplicate outlets are collapsed.
- Skeletons: While loading, render premium placeholder cards displaying pulsing grey blocks in place of titles and details.
- Restaurant Cards: Premium glass cards with:
  * Rank Badge: Circular gold badge for top 3 ("#1", "#2", "#3"), and Zomato Red for others.
  * AI Status Badge: Glossy "🤖 AI Ranked" or fallback "📊 Ranked by Rating" pill tag.
  * Cuisine Tags: Horizontal flow of pill chips (e.g., "North Indian", "Chinese").
  * Metadata Row: Star ratings, cost indicators ("💰 ₹800 for two"), and geographic pins ("📍 Indiranagar").
  * AI Explanation Block: Clean quotes showing description, with a "↓ Read more / ↑ Show less" toggler for text longer than 180 characters.

### 5. SYSTEM CRASH FALLBACK (ErrorBoundary.tsx)
- Include a sleek, full-screen crash panel containing a "⚠ Something went wrong" warning, complete technical detail toggler (collapsible terminal box), and a reloading action button matching the application theme.
```

---

## 🚀 PART 2: STITCH DEPLOYMENT SPECIFICATIONS (NODE.JS)
*(Useful when configuring deployment runs and environment settings on your host pipeline)*

| Parameter | Specification |
|-----------|---------------|
| **Runtime Environment** | **Node.js v18+ / v20+** |
| **Framework Runtime** | Express.js (Node.js Web Server) |
| **Build Command** | `npm run build` |
| **Start Command** | `npm start` |
| **Default Port** | `5173` (Stitch overrides dynamically using `process.env.PORT`) |
| **Static Build Folder** | `dist/` |

---

## 📄 PART 3: NODE.JS CONFIGURATION FILES

### 1. `package.json`
The application's `package.json` includes `express` to serve the Vite-compiled static assets and run production SPA route fallback:

```json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview",
    "test": "vitest",
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.19.2",
    "react": "^19.2.6",
    "react-dom": "^19.2.6"
  }
}
```

### 2. Node.js Production Server (`server.js`)
This script executes under the Node runtime to deliver high-performance asset distribution:

```javascript
import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 5173;

// Serve static assets compiled by Vite
app.use(express.static(path.join(__dirname, 'dist')));

// Fallback to index.html to support React SPA client-side routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server successfully started on port ${PORT}`);
  console.log(`Serving static files from: ${path.join(__dirname, 'dist')}`);
});
```
