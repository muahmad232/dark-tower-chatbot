# KaGuide Frontend

React frontend for the Dark Tower Chatbot.

## Vercel Deployment

### Quick Deploy

1. Import this repository to Vercel
2. Set **Root Directory** to `frontend`
3. Framework will be auto-detected as Create React App
4. Add Environment Variable:
   - `REACT_APP_API_URL` = `https://your-backend-url.onrender.com`
5. Deploy!

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | `https://dark-tower-api.onrender.com` |

### Local Development

```bash
# Install dependencies
npm install

# Create .env file
cp .env.example .env
# Edit .env with your local backend URL

# Start development server
npm start
```

### Build

```bash
npm run build
```

Output will be in the `build` folder.

## Tech Stack

- React 19
- React Router v7
- Custom CSS with CSS Variables
- Cinzel & Crimson Text fonts
