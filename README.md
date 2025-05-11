# Video Recommendation Engine

A FastAPI-based video recommendation system that connects to the EmpowerVerse API to provide personalized video recommendations.

## Features

- **Personalized Recommendations**: Get video recommendations based on user interactions and preferences
- **API Caching**: Reduces load on the EmpowerVerse API and improves response times
- **Fallback System**: Gracefully handles API errors by using cached or synthetic data
- **Advanced Recommendation Algorithm**: Uses content-based and collaborative filtering approaches

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd video-recommendation-assignment
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API credentials:
   ```
   API_BASE_URL=https://api.socialverseapp.com
   FLIC_TOKEN=your_flic_token_here
   RESONANCE_ALGORITHM=your_resonance_algorithm_here
   
   # Optional settings
   PORT=8000
   HOST=127.0.0.1
   USE_FALLBACK=true
   USE_CACHE=true
   REQUEST_TIMEOUT=5.0
   ```

## Usage

### Starting the Server

Run the application with:

```bash
python run.py
```

The server will start on the configured port (default: 8000) or find an available port automatically if the default is in use.

### API Endpoints

- **GET /api/feed?username={username}**: Get personalized recommendations for a specific user
- **GET /api/kinha-feed**: Get recommendations specifically for user "kinha"
- **GET /api/universal-feed?username={username}**: Get recommendations for any username (real or synthetic)

### Control Endpoints

- **GET /api/test**: Test connection to the EmpowerVerse API
- **GET /api/fallback?enable={true|false}**: Enable/disable fallback mode
- **GET /api/cache?enable={true|false}**: Enable/disable caching
- **GET /api/cache/clear**: Clear all cached data
- **GET /api/cache/clear?key={cache_key}**: Clear specific cached data

## Configuration

The application can be configured through environment variables or the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| API_BASE_URL | EmpowerVerse API URL | https://api.socialverseapp.com |
| FLIC_TOKEN | Authentication token | - |
| PORT | Server port | 8000 |
| HOST | Server host | 127.0.0.1 |
| REQUEST_TIMEOUT | API request timeout in seconds | 5.0 |
| USE_FALLBACK | Enable fallback mode | true |
| USE_CACHE | Enable caching | true |
| CACHE_TTL | Cache time-to-live in seconds | 3600 |

## Recommendation Algorithm

The recommendation engine uses a combination of:

- User interaction history (views, likes, ratings)
- Content similarity (tags, categories, project codes)
- Creator preferences
- Mood-based matching
- Popularity metrics
- Content recency

## Troubleshooting

### Port Already in Use

If the default port is already in use, the application will automatically find an available port. You can also specify a different port in the `.env` file or as an environment variable.

### API Connection Issues

If the application cannot connect to the EmpowerVerse API, it will use fallback data or cached responses. You can check the API connection status with the `/api/test` endpoint.

## Data Caching

The application caches API responses to reduce load on the EmpowerVerse API and improve response times. Cached data expires after 1 hour by default.
