"""
Analiza Rynku Pracy i Wynagrodzeń w Polsce
Flask Application — Projekt Zaliczeniowy WSB Merito
Autor: Mateusz Mazur (nr albumu: 137683)

Źródło danych: Główny Urząd Statystyczny (GUS)
- Bank Danych Lokalnych: https://bdl.stat.gov.pl
- Komunikaty i obwieszczenia: https://stat.gov.pl
"""

import os
import json
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'gus-projekt-wsb-merito-2025-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Zaloguj się, aby uzyskać dostęp do analizy.'
login_manager.login_message_category = 'info'

# ---------------------------------------------------------------------------
# Database Model
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def load_data():
    """Wczytuje wszystkie pliki CSV z katalogu data/."""
    data = {}
    data['wynagrodzenia'] = pd.read_csv(os.path.join(DATA_DIR, 'wynagrodzenia_polska.csv'))
    data['bezrobocie'] = pd.read_csv(os.path.join(DATA_DIR, 'bezrobocie_woj.csv'))
    data['pkd'] = pd.read_csv(os.path.join(DATA_DIR, 'zatrudnienie_pkd.csv'))
    data['luka'] = pd.read_csv(os.path.join(DATA_DIR, 'luka_placowa.csv'))
    return data


# ---------------------------------------------------------------------------
# Chart Generation (Plotly)
# ---------------------------------------------------------------------------
CHART_TEMPLATE = 'plotly_dark'
COLOR_ACCENT = '#00d4aa'
COLOR_SECONDARY = '#6366f1'
COLOR_WARN = '#f59e0b'
COLOR_DANGER = '#ef4444'


def chart_to_json(fig):
    """Serializuje figurę Plotly do JSON (do osadzenia w Jinja2)."""
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def make_salary_trend(df):
    """Wykres 1: Trend wynagrodzeń nominalnych i realnych."""
    # Oblicz wynagrodzenie realne (deflacja CPI, baza 2015)
    skumulowana = (1 + df['Inflacja_CPI_procent'] / 100).cumprod()
    df = df.assign(
        Skumulowana_inflacja=skumulowana,
        Wynagrodzenie_realne_PLN=df['Wynagrodzenie_brutto_PLN'] / skumulowana * skumulowana.iloc[0]
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Rok'], y=df['Wynagrodzenie_brutto_PLN'],
        name='Nominalne', mode='lines+markers',
        line=dict(color=COLOR_ACCENT, width=3),
        marker=dict(size=8),
        hovertemplate='%{x}<br>%{y:,.0f} PLN<extra>Nominalne</extra>'
    ))
    fig.add_trace(go.Scatter(
        x=df['Rok'], y=df['Wynagrodzenie_realne_PLN'],
        name='Realne (baza 2015)', mode='lines+markers',
        line=dict(color=COLOR_SECONDARY, width=3, dash='dash'),
        marker=dict(size=8),
        hovertemplate='%{x}<br>%{y:,.0f} PLN<extra>Realne</extra>'
    ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title=dict(text='Przeciętne wynagrodzenie brutto w sektorze przedsiębiorstw (2015–2024)',
                   font=dict(size=16)),
        xaxis_title='Rok',
        yaxis_title='PLN brutto / miesiąc',
        yaxis_tickformat=',',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=20, t=80, b=60),
        height=450,
    )
    return chart_to_json(fig)


def make_salary_yoy(df):
    """Wykres 2: Dynamika r/r wynagrodzeń vs inflacja CPI."""
    df = df.assign(Dynamika_wynagrodzen=df['Wynagrodzenie_brutto_PLN'].pct_change() * 100).dropna()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['Rok'], y=df['Dynamika_wynagrodzen'],
        name='Wzrost wynagrodzeń (%)',
        marker_color=COLOR_ACCENT,
        hovertemplate='%{x}<br>+%{y:.1f}%<extra>Wynagrodzenia</extra>'
    ))
    fig.add_trace(go.Scatter(
        x=df['Rok'], y=df['Inflacja_CPI_procent'],
        name='Inflacja CPI (%)',
        mode='lines+markers',
        line=dict(color=COLOR_DANGER, width=3),
        marker=dict(size=8),
        hovertemplate='%{x}<br>%{y:.1f}%<extra>CPI</extra>'
    ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title=dict(text='Dynamika wzrostu wynagrodzeń vs. inflacja CPI (r/r)', font=dict(size=16)),
        xaxis_title='Rok',
        yaxis_title='%',
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=20, t=80, b=60),
        height=420,
    )
    return chart_to_json(fig)


def make_unemployment_heatmap(df):
    """Wykres 3: Mapa cieplna bezrobocia wg województw."""
    years = [str(y) for y in range(2015, 2025)]
    woj = df['Województwo'].tolist()
    z_data = df[years].values.tolist()

    fig = go.Figure(data=go.Heatmap(
        z=z_data, x=years, y=woj,
        colorscale=[[0, '#0d2137'], [0.3, '#1a5276'], [0.5, '#2e86c1'], [0.7, '#f39c12'], [1, '#e74c3c']],
        hovertemplate='%{y}<br>Rok: %{x}<br>Bezrobocie: %{z:.1f}%<extra></extra>',
        colorbar=dict(title=dict(text='%', side='right'))
    ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title=dict(text='Stopa bezrobocia rejestrowanego wg województw (2015–2024)', font=dict(size=16)),
        xaxis_title='Rok',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=180, r=20, t=80, b=60),
        height=580,
    )
    return chart_to_json(fig)


def make_unemployment_national(df_woj, df_main):
    """Wykres 4: Stopa bezrobocia ogólnopolska (trend)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_main['Rok'], y=df_main['Stopa_bezrobocia_procent'],
        mode='lines+markers+text',
        text=[f'{v}%' for v in df_main['Stopa_bezrobocia_procent']],
        textposition='top center',
        textfont=dict(size=11, color=COLOR_ACCENT),
        line=dict(color=COLOR_ACCENT, width=3),
        marker=dict(size=10, color=COLOR_ACCENT),
        hovertemplate='%{x}<br>%{y:.1f}%<extra></extra>',
        showlegend=False
    ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title=dict(text='Stopa bezrobocia rejestrowanego w Polsce (2015–2024)', font=dict(size=16)),
        xaxis_title='Rok',
        yaxis_title='%',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=20, t=80, b=60),
        height=380,
    )
    return chart_to_json(fig)


def make_pkd_comparison(df):
    """Wykres 5: Porównanie wynagrodzeń wg sekcji PKD (2020 vs 2024)."""
    df_sorted = df.sort_values('Wynagrodzenie_2024_PLN', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sorted['Nazwa'], x=df_sorted['Wynagrodzenie_2020_PLN'],
        name='2020', orientation='h',
        marker_color=COLOR_SECONDARY,
        hovertemplate='%{y}<br>2020: %{x:,.0f} PLN<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        y=df_sorted['Nazwa'], x=df_sorted['Wynagrodzenie_2024_PLN'],
        name='2024', orientation='h',
        marker_color=COLOR_ACCENT,
        hovertemplate='%{y}<br>2024: %{x:,.0f} PLN<extra></extra>'
    ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title=dict(text='Wynagrodzenia brutto wg sekcji PKD: 2020 vs 2024', font=dict(size=16)),
        xaxis_title='PLN brutto / miesiąc',
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=300, r=20, t=80, b=60),
        height=650,
    )
    return chart_to_json(fig)


def make_gender_gap(df):
    """Wykres 6: Luka płacowa i trend."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=df['Rok'], y=df['Wynagrodzenie_mezczyzni_PLN'],
        name='Mężczyźni', marker_color=COLOR_SECONDARY,
        hovertemplate='%{x}<br>%{y:,.0f} PLN<extra>Mężczyźni</extra>'
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=df['Rok'], y=df['Wynagrodzenie_kobiety_PLN'],
        name='Kobiety', marker_color='#ec4899',
        hovertemplate='%{x}<br>%{y:,.0f} PLN<extra>Kobiety</extra>'
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df['Rok'], y=df['Luka_placowa_procent'],
        name='Luka płacowa (%)', mode='lines+markers',
        line=dict(color=COLOR_WARN, width=3),
        marker=dict(size=8),
        hovertemplate='%{x}<br>%{y:.1f}%<extra>Luka</extra>'
    ), secondary_y=True)

    fig.update_layout(
        template=CHART_TEMPLATE,
        title=dict(text='Luka płacowa między kobietami a mężczyznami (2015–2024)', font=dict(size=16)),
        xaxis_title='Rok',
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=60, t=80, b=60),
        height=450,
    )
    fig.update_yaxes(title_text='PLN brutto / miesiąc', secondary_y=False)
    fig.update_yaxes(title_text='Luka (%)', secondary_y=True)

    return chart_to_json(fig)


def make_pkd_employment_change(df):
    """Wykres 7: Zmiana zatrudnienia wg PKD (2020 → 2024)."""
    df = df.assign(Zmiana_procent=((df['Zatrudnienie_2024_tys'] - df['Zatrudnienie_2020_tys']) / df['Zatrudnienie_2020_tys'] * 100).round(1))
    df_sorted = df.sort_values('Zmiana_procent', ascending=True)

    colors = [COLOR_ACCENT if v >= 0 else COLOR_DANGER for v in df_sorted['Zmiana_procent']]

    fig = go.Figure(go.Bar(
        y=df_sorted['Nazwa'],
        x=df_sorted['Zmiana_procent'],
        orientation='h',
        marker_color=colors,
        text=[f'{v:+.1f}%' for v in df_sorted['Zmiana_procent']],
        textposition='outside',
        hovertemplate='%{y}<br>Zmiana: %{x:+.1f}%<extra></extra>'
    ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title=dict(text='Zmiana zatrudnienia wg sekcji PKD (2020 → 2024)', font=dict(size=16)),
        xaxis_title='Zmiana (%)',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=300, r=80, t=80, b=60),
        height=580,
    )
    return chart_to_json(fig)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        # Walidacja
        errors = []
        if len(username) < 3:
            errors.append('Nazwa użytkownika musi mieć min. 3 znaki.')
        if '@' not in email or '.' not in email:
            errors.append('Podaj poprawny adres e-mail.')
        if len(password) < 6:
            errors.append('Hasło musi mieć min. 6 znaków.')
        if password != password2:
            errors.append('Hasła nie są identyczne.')
        if User.query.filter_by(username=username).first():
            errors.append('Ta nazwa użytkownika jest już zajęta.')
        if User.query.filter_by(email=email).first():
            errors.append('Ten adres e-mail jest już zarejestrowany.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html', username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Konto utworzone pomyślnie! Możesz się teraz zalogować.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(remember))
            next_page = request.args.get('next')
            flash(f'Witaj, {user.username}!', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś wylogowany.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    data = load_data()

    charts = {
        'salary_trend': make_salary_trend(data['wynagrodzenia']),
        'salary_yoy': make_salary_yoy(data['wynagrodzenia']),
        'unemployment_heatmap': make_unemployment_heatmap(data['bezrobocie']),
        'unemployment_national': make_unemployment_national(data['bezrobocie'], data['wynagrodzenia']),
        'pkd_comparison': make_pkd_comparison(data['pkd']),
        'gender_gap': make_gender_gap(data['luka']),
        'pkd_employment': make_pkd_employment_change(data['pkd']),
    }

    # Key stats for the summary cards
    df_w = data['wynagrodzenia']
    latest = df_w.iloc[-1]
    prev = df_w.iloc[-2]
    salary_change = ((latest['Wynagrodzenie_brutto_PLN'] - prev['Wynagrodzenie_brutto_PLN']) / prev['Wynagrodzenie_brutto_PLN'] * 100)

    stats = {
        'latest_salary': f"{latest['Wynagrodzenie_brutto_PLN']:,.0f}",
        'salary_year': int(latest['Rok']),
        'salary_change': f"{salary_change:+.1f}",
        'unemployment': f"{latest['Stopa_bezrobocia_procent']:.1f}",
        'inflation': f"{latest['Inflacja_CPI_procent']:.1f}",
        'gender_gap': f"{data['luka'].iloc[-1]['Luka_placowa_procent']:.1f}",
    }

    return render_template('dashboard.html', charts=charts, stats=stats)


@app.route('/methodology')
@login_required
def methodology():
    return render_template('methodology.html')


# ---------------------------------------------------------------------------
# Init DB & Run
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
