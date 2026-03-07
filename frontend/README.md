# Frontend

React single-page application providing generic UI for all apps.

## Architecture

**Schema-driven**: All components are generic and render based on schema definitions. No app-specific code.

## Files

### Core (`src/`)
- **`App.jsx`** (~100 lines) - Router setup, schema loading, navigation
- **`ListView.jsx`** (~150 lines) - Generic list view for any app
- **`FormView.jsx`** (~150 lines) - Generic create/edit form for any app
- **`styles.css`** (~100 lines) - Mobile-first responsive styles

### Components (`src/components/`)
- **`FieldRenderer.jsx`** (~80 lines) - Render field by type (text, date, select, etc.)
- **`Navbar.jsx`** (~40 lines) - Navigation bar with app links

**Total:** ~620 lines of JavaScript/CSS

## Routing

```
/                    - Home page (list of apps)
/{app_id}            - List view for app
/{app_id}/new        - Create new item
/{app_id}/edit/:id   - Edit existing item
```

Routes are generated dynamically based on loaded schemas.

## Mobile-First Design

**All components must be mobile-friendly:**
- Base styles for 375px width
- Touch targets minimum 44px
- No horizontal scrolling
- Progressive enhancement for larger screens

**CSS strategy:**
```css
/* Mobile first (default) */
.list-item {
  flex-direction: column;
}

/* Tablet+ */
@media (min-width: 768px) {
  .list-item {
    flex-direction: row;
  }
}
```

## Dependencies

```
react
react-dom
react-router-dom
vite (build tool)
```

## Running Locally

```bash
cd frontend
npm install
npm run dev
```

Access at http://localhost:5173

## Building for Production

```bash
npm run build
# Output: dist/ directory
```

## Code Guidelines

- Each file has one responsibility (see CLAUDE.md)
- Max 400 lines per file (500 hard limit)
- Use camelCase for functions/variables
- Use PascalCase for components
- No app-specific logic - all rendering is schema-driven
- Test on mobile viewport (375px) for every change
