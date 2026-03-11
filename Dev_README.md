# NotaRAG

A React-based application built with Vite, TypeScript, and Shadcn/ui.

## Getting Started

### Prerequisites

- Node.js & npm - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/CREATE-UofT/NotaRAG.git
   cd NotaRAG
   ```

2. Install dependencies:
   ```sh
   npm install
   ```

3. Start the development server:
   ```sh
   npm run dev
   ```

The application will be available at `http://localhost:5173` (or another port if 5173 is in use).

##
## How can I edit this code?


**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## Environment variables (important)

This project uses Vite for the frontend and a Python FastAPI backend. Secrets must never be committed. Create local env files as described below.

- Frontend (client-visible): create `.env.local` in the project root (this file is ignored by git).
  - Required variables (example):
    ```
    VITE_SUPABASE_URL=https://your-project.supabase.co
    VITE_SUPABASE_ANON_KEY=your_supabase_anon_public_key
    ```
  
  - Notes:
   - You can get these from our supabase project, supabase url is found on api docs, and anon key is in settings - > api keys -> anon key
   - Use the "anon/public" key from Supabase (not the service_role key).
   - Restart the dev server after editing `.env.local`: `npm run dev`.


