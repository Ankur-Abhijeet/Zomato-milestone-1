# Stitch UI Generation Spec & Deployment Prompt: Zomato Light Theme SPA

Use this document as a **High-Fidelity Input Prompt** for AI UI Generators (such as Stitch, v0, or Bolt) to generate the exact webpage look, aesthetic, interactions, and responsive components of the Zomato-inspired light theme application. 

Additionally, it contains standard **Node.js Express Deployment Specs** to host and serve the React Single Page Application (SPA) inside the production environment.

---

## 🚀 PART 1: STITCH WEB UI GENERATION PROMPT
*(Paste the block below directly into your UI generation tool to output the exact webpage look)*

```text
Create a premium, modern, responsive Zomato-inspired light-mode React web application for an AI-Powered Restaurant Recommendation System. Follow these strict visual tokens, components, and layout structures to produce the exact UI look matching the screenshot:

### 1. DESIGN SYSTEM & DESIGN TOKENS (Sleek Light Theme)
- Font Family: 'Inter', system-ui, sans-serif (imported from Google Fonts).
- Primary Background: Soft blueish-gray page background (#f4f5f7) with elegant gray scrollbars.
- Surface Cards Backdrop: Clean solid white surfaces (#ffffff) with subtle borders (#e5e7eb) and shadow-sm.
- Accent Color: Vibrant Zomato Red (#e23744) with hover transition (#c9202e).
- Text Colors: Dark charcoal slate (#111827 or #1f2937) for primary text; medium gray (#4b5563) for subtitles.
- Animations: Smooth fade-in staggered transitions for card list entry.

### 2. PAGE LAYOUT (Home.tsx)
- The layout is a modern single-page dashboard.
- Desktop view: A two-column grid. Left side has a sticky sidebar for options search or active picks (360px wide). Right side has the scrolling results column with light gray background (#f4f5f7).
- Mobile view: A single column stack with the options form nested on top, folding into cards gracefully.
- Top Header Bar: White background (#ffffff) with a 1px bottom border. Contains:
  * Left: Bold italic black "zomato" logo, next to a small CPU outline AI badge.
  * Center: Centered search bar with rounded borders, a search icon inside, and "Search" placeholder.
  * Right: Circular gray user profile outline button.

### 3. INTERACTIVE SEARCH FORM (PreferenceForm.tsx)
- Location Input: High-contrast input field with red asterisk (*) for required state. Contains placeholders and alert warning tags underneath.
- Budget Selection Group: 3 large horizontal pill buttons:
  * "💸 Low" (displays label and description: "≤ ₹500" inline).
  * "💳 Medium" (marked active by default using Zomato Red outline glow).
  * "💎 High" (displays label and description: "> ₹1,500").
- Cuisine Chip Manager: Search bar where pressing "Enter" or "," adds custom keywords as tag chips (e.g. "Italian", "Continental"). Tags contain a distinct round "×" delete button that changes state on hover.
- Minimum Rating Slider: A range slider (0.0 to 5.0 in 0.5 steps) decorated with an active Zomato Red gradient track, and a live text badge indicating the stars (e.g. "⭐ 4.5").
- Top-K stepper: Custom adjustment buttons ("−" and "+") with a live digital count display centered.
- Submit Button: A wide button that elevates slightly on hover. If loading is triggered, it replaces text with a spinning loader and shows "Finding your perfect spots...".

### 4. RECOMMENDATIONS LAYOUT (ResultsView.tsx & RestaurantCard.tsx)
- Reasoning Summary Panel: Rendered in the left sidebar once results load.
  * A soft peach/pink box (#feeceb) with rounded corners (12px).
  * A beautiful outline SVG brain icon on the left.
  * Red text "Reasoning Summary: Here's why these are perfect for you:..." explaining recommendations.
- Filter Pills Panel: Below the reasoning bubble, a vertical stack of white rectangular pills with thin borders:
  * "Cuisine: Indian, Mexican, Thai"
  * "Price: $$"
  * "Vibe: Casual"
  * "Location: New York City"
  * "Rating: 4.0+"
- Restaurant Cards: Premium white cards (#ffffff) resting on the light gray results background, featuring:
  * Image Aspect Ratio: Rounded top-left/top-right corners with high-fidelity cuisine images (chicken curry, tacos, ramen).
  * Name & Ratings Row: **Inline on a single line!** Bold name on the left (e.g., "Spice Route Kitchen"), and rating/match details on the right: "4.5 ★ (520 ratings) • 98% Match" (gold star, gray ratings count, red Match percentage).
  * Cuisines Line: Comma-separated gray text immediately below the title-rating row.
  * AI Explanation Block: Soft gray/blue-gray background block (#f4f6f8) with a CPU outline SVG icon on the left, "Why this fits: ..." text in the center, and a white "View Details" button on the right.

### 5. STICKY BOTTOM FOOTER BAR
- Centered layout with white background and thin gray border:
  * Left: A wide pill-shaped input chat box with placeholder "Ask me about their best dish...", containing a nested light-gray "Send" button on the right.
  * Right: A solid crimson red pill button (#e23744) with white text: "Book a Table".
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
