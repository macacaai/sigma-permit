# Sigma Permit Frontend

A modern SvelteKit frontend for the Sigma Permit license management system.

## Features

- **Modern UI**: Built with SvelteKit, TypeScript, and Tailwind CSS
- **Responsive Design**: Mobile-first design that works on all devices
- **Real-time Updates**: Live data updates with toast notifications
- **Type Safety**: Full TypeScript support for better development experience
- **Component Architecture**: Reusable components for consistent UI
- **API Integration**: Seamless integration with FastAPI backend

## Tech Stack

- **Framework**: SvelteKit 2.0
- **Language**: TypeScript
- **Styling**: Tailwind CSS (Custom Design System)
- **Icons**: Lucide Svelte
- **Forms**: Svelte Forms Lib
- **Notifications**: Svelte French Toast
- **Loading**: Svelte Loading Spinners

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- FastAPI backend running on `http://localhost:8000`

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   Navigate to `http://localhost:5173`

### Build for Production

```bash
npm run build
npm run preview
```

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run check` - Type checking and linting
- `npm run format` - Format code with Prettier

## Project Structure

```
frontend/
├── src/
│   ├── lib/api.ts          # API client for FastAPI backend
│   ├── components/         # Reusable UI components
│   │   ├── Modal.svelte    # Reusable modal component
│   │   ├── Navigation.svelte # Sidebar navigation
│   │   └── TenantForm.svelte # Tenant CRUD form
│   ├── routes/             # Page routes
│   │   ├── +layout.svelte  # Root layout
│   │   ├── +page.svelte    # Dashboard
│   │   └── tenants/        # Tenants management
│   ├── app.css             # Global styles with Tailwind
│   └── app.html            # HTML template
├── tailwind.config.js      # Tailwind CSS configuration
├── postcss.config.js       # PostCSS configuration
├── package.json            # Dependencies & scripts
├── svelte.config.js        # SvelteKit config
├── tsconfig.json           # TypeScript config
├── vite.config.ts          # Build config with API proxy
└── README.md               # This file
```

## Features Overview

### Dashboard
- System health monitoring
- Statistics overview (tenants, templates, licenses)
- Quick action buttons
- Getting started guide

### Tenants Management (Full CRUD)
- **View**: Paginated table with search/filtering
- **Create**: Modal form with auto-slug generation
- **Edit**: Inline editing with validation
- **Delete**: Confirmation modal with warnings
- **Status**: Active/inactive status management

### Templates Management (Coming Soon)
- JSON schema validation
- Template library
- License generation from templates

### Licenses Management (Coming Soon)
- Bulk operations
- Template-based creation
- Tenant filtering
- Expiration tracking

## Styling & Design

### Design System
- **Colors**: Custom color palette with primary, secondary, tertiary variants
- **Typography**: Inter font family for modern appearance
- **Components**: Consistent button, form, table, and modal styles
- **Dark Mode**: Class-based dark mode support

### Responsive Design
Mobile-first approach with breakpoints:
- `sm:` 640px and up
- `md:` 768px and up
- `lg:` 1024px and up
- `xl:` 1280px and up

## API Integration

The frontend includes a comprehensive API client that handles:

- **Automatic Error Handling**: Toast notifications for API errors
- **Type Safety**: Full TypeScript support for API responses
- **Loading States**: Built-in loading indicators
- **Request/Response Interception**: Centralized API logic

```typescript
// Example usage
import { tenantApi } from '$lib/api';

const tenants = await tenantApi.getTenants(1, 10);
await tenantApi.createTenant(newTenantData);
```

## Development Tips

- Use `npm run check:watch` for continuous type checking
- Enable browser dev tools for debugging
- Leverage SvelteKit's file-based routing
- Use Svelte's reactive statements for efficient updates

## Troubleshooting

### Common Issues

1. **API Connection Issues**
   - Ensure FastAPI backend is running on port 8000
   - Check CORS settings in FastAPI
   - Verify API endpoints match frontend expectations

2. **Styling Issues**
   - Verify Tailwind classes are correct
   - Check that Tailwind config includes all source files
   - Ensure PostCSS is processing correctly

3. **Build Errors**
   - Run `npm run check` for TypeScript errors
   - Ensure all dependencies are installed
   - Check Node.js version compatibility

## Contributing

1. Follow TypeScript strict mode
2. Use Prettier for code formatting
3. Write meaningful commit messages
4. Test components thoroughly
5. Follow Svelte and SvelteKit best practices

## License

This project is part of the Sigma Permit license management system.
