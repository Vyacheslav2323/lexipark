# Jorp - Korean Vocabulary Learning Platform

A Django-based web application for learning Korean vocabulary through interactive text analysis and spaced repetition.

## Features

- **Interactive Text Analysis**: Upload Korean text and get word-by-word analysis
- **Vocabulary Management**: Save Korean words with translations and grammar information
- **Spaced Repetition**: Bayesian recall system for optimal learning
- **Hover Tracking**: Track how long users hover over words to measure familiarity
- **Translation Integration**: Automatic translation using Papago API
- **User Authentication**: User profiles and personalized vocabulary lists

## Technology Stack

- **Backend**: Django 5.2.4
- **Frontend**: Bootstrap 5, JavaScript
- **Database**: SQLite (development), PostgreSQL (production)
- **Korean NLP**: MeCab for morphological analysis
- **Translation**: Papago API integration

## Installation

### Prerequisites

- Python 3.8+
- MeCab (for Korean text analysis)
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Vyacheslav2323/lexipark.git
   cd lexipark
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install MeCab** (for Korean text analysis)
   - **macOS**: `brew install mecab mecab-ko mecab-ko-dic`
   - **Ubuntu**: `sudo apt-get install mecab mecab-ko mecab-ko-dic`
   - **Windows**: Download from [MeCab website](https://taku910.github.io/mecab/)

5. **Install Python MeCab**
   ```bash
   pip install mecab-python3
   ```

6. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   SECRET_KEY=your-secret-key
   DEBUG=True
   DATABASE_URL=sqlite:///db.sqlite3
   PAPAGO_CLIENT_ID=your-papago-client-id
   PAPAGO_CLIENT_SECRET=your-papago-client-secret
   ```

7. **Run migrations**
   ```bash
   python manage.py migrate
   ```

8. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

9. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## Usage

1. **Register/Login**: Create an account or log in
2. **Text Analysis**: Go to the analysis page and paste Korean text
3. **Word Learning**: Click on Korean words to save them to your vocabulary
4. **Review**: Check your profile to see your vocabulary list with retention rates

## Project Structure

```
jorp/
├── analysis/          # Text analysis app
├── users/            # User authentication app
├── vocab/            # Vocabulary management app
├── jorp/             # Main Django settings
├── alternative_translators.py  # Translation services
└── manage.py         # Django management script
```

## API Integration

The project integrates with Papago Translation API for Korean-English translations. See `PAPAGO_INTEGRATION.md` for setup details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email [your-email] or create an issue in the GitHub repository. 