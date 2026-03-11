# Files Explainer

This document explains the structure and purpose of each file in the project.

## Root Configuration Files

- **README.md** - Project documentation with setup instructions and deployment info
- **index.html** - HTML entry point for the Vite application
- **vite.config.ts** - Vite bundler configuration
- **tailwind.config.ts** - Tailwind CSS configuration with design tokens
- **eslint.config.js** - ESLint configuration for code linting
- **tsconfig.json** - TypeScript compiler configuration

## Public Directory

- **public/robots.txt** - SEO file for web crawlers
- **public/favicon.ico** - Browser tab icon

## Source Directory Structure

### Core Application Files

- **src/main.tsx** - Application entry point, renders the root React component
- **src/App.tsx** - Main app component with routing configuration
- **src/App.css** - Global app styles
- **src/index.css** - Global styles with design system tokens and Tailwind directives
- **src/vite-env.d.ts** - TypeScript definitions for Vite

### Pages (`src/pages/`)

- **Index.tsx** - Landing/home page
- **Auth.tsx** - Authentication page for login/signup
- **Dashboard.tsx** - Main dashboard with notes, folders, starred items, and recent activity
- **Editor.tsx** - Note editor page with chat functionality
- **Search.tsx** - Search interface for finding notes
- **Chat.tsx** - Dedicated chat interface
- **NotFound.tsx** - 404 error page

### Components (`src/components/`)

- **NoteChat.tsx** - Chat interface component for conversing with notes

### UI Components (`src/components/ui/`)

All shadcn/ui components for consistent design:

- **button.tsx** - Button component with variants
- **card.tsx** - Card container component
- **input.tsx** - Text input field
- **textarea.tsx** - Multi-line text input
- **dialog.tsx** - Modal dialog
- **dropdown-menu.tsx** - Dropdown menu for actions
- **tabs.tsx** - Tab navigation component
- **badge.tsx** - Badge/tag component
- **avatar.tsx** - User avatar component
- **toast.tsx** / **toaster.tsx** / **use-toast.ts** - Toast notification system
- **label.tsx** - Form label component
- **progress.tsx** - Progress bar component
- **hover-card.tsx** - Hover card for additional info
- **accordion.tsx** - Collapsible accordion
- **alert.tsx** / **alert-dialog.tsx** - Alert components
- **calendar.tsx** - Date picker calendar
- **checkbox.tsx** - Checkbox input
- **select.tsx** - Select dropdown
- **slider.tsx** - Range slider
- **switch.tsx** - Toggle switch
- **table.tsx** - Data table
- **tooltip.tsx** - Tooltip component
- **sheet.tsx** - Slide-out panel
- **sidebar.tsx** - Sidebar navigation
- **scroll-area.tsx** - Custom scrollable area
- **separator.tsx** - Visual divider
- **skeleton.tsx** - Loading skeleton
- **form.tsx** - Form wrapper with validation
- **command.tsx** - Command palette
- **context-menu.tsx** - Right-click context menu
- **menubar.tsx** - Menu bar navigation
- **navigation-menu.tsx** - Navigation menu
- **pagination.tsx** - Pagination controls
- **popover.tsx** - Popover container
- **radio-group.tsx** - Radio button group
- **resizable.tsx** - Resizable panels
- **toggle.tsx** / **toggle-group.tsx** - Toggle buttons
- **aspect-ratio.tsx** - Aspect ratio container
- **breadcrumb.tsx** - Breadcrumb navigation
- **carousel.tsx** - Image carousel
- **chart.tsx** - Chart components
- **collapsible.tsx** - Collapsible content
- **drawer.tsx** - Drawer panel
- **input-otp.tsx** - OTP input field
- **sonner.tsx** - Toast notifications

### Utilities (`src/lib/`)

- **utils.ts** - Utility functions including `cn()` for class name merging

### Hooks (`src/hooks/`)

- **use-mobile.tsx** - Hook to detect mobile viewport
- **use-toast.ts** - Hook for toast notifications

### Assets (`src/assets/`)

- **hero-background.jpg** - Hero section background image

## Key Features by File

### Dashboard.tsx
- Folder management (create, select, delete)
- Note management (create, star, delete, move between folders)
- Recent activity tracking
- Tabbed interface (All Notes, Starred, Recent)
- Note filtering by folder

### Editor.tsx
- Rich text editing interface
- Note chat integration (chat with note content)
- Sliding chat panel on the right side

### NoteChat.tsx
- Chat interface for AI conversations about notes
- Message history display
- Input field for user messages
- Ready for Lovable Cloud integration

### Auth.tsx
- User authentication interface
- Login/signup forms
