import logging
from datetime import datetime
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)
app.secret_key = 'chiave_segreta_super_segreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hosts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)

class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    interval = db.Column(db.Integer, default=10)
    active = db.Column(db.Boolean, default=True)
    last_check = db.Column(db.DateTime, nullable=True)
    last_status = db.Column(db.Integer, nullable=True)
    last_response_time = db.Column(db.Float, nullable=True)

# --- LOGICA CORE ---
def perform_single_ping(host):
    """Esegue il ping di un singolo host e aggiorna i dati (senza commit)"""
    try:
        # User agent personalizzato per evitare blocchi
        response = requests.get(host.url, timeout=10, headers={'User-Agent': 'KeepAliveBot/2.0'})
        host.last_status = response.status_code
        host.last_response_time = round(response.elapsed.total_seconds() * 1000, 0)
    except requests.RequestException:
        host.last_status = 0 # 0 = Errore
        host.last_response_time = 0
    
    host.last_check = datetime.now()

def check_hosts():
    """Task periodico schedulato"""
    with app.app_context():
        hosts = Host.query.filter_by(active=True).all()
        now = datetime.now()
        changes = False
        
        for host in hosts:
            should_check = False
            if not host.last_check:
                should_check = True
            else:
                # Calcolo differenza minuti
                diff = (now - host.last_check).total_seconds() / 60
                if diff >= host.interval:
                    should_check = True
            
            if should_check:
                logger.info(f"Auto-Pinging {host.name}...")
                perform_single_ping(host)
                changes = True
        
        if changes:
            db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_hosts, trigger="interval", seconds=10) # Controllo ogni 10s
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# --- ROUTES UI ---
@app.route('/')
def index():
    hosts = Host.query.order_by(Host.id.desc()).all()
    return render_template('index.html', hosts=hosts)

# --- API PER AGGIORNAMENTO REAL-TIME ---
@app.route('/api/status')
def api_status():
    """Restituisce JSON con lo stato attuale di tutti gli host"""
    hosts = Host.query.all()
    data = []
    for h in hosts:
        # Formattazione data
        check_str = h.last_check.strftime('%H:%M:%S') if h.last_check else 'Mai'
        
        data.append({
            'id': h.id,
            'last_status': h.last_status,
            'last_response_time': h.last_response_time,
            'last_check': check_str,
            'active': h.active
        })
    return jsonify(data)

@app.route('/api/ping/<int:id>', methods=['POST'])
def api_manual_ping(id):
    """Ping manuale triggered dall'utente"""
    host = Host.query.get_or_404(id)
    perform_single_ping(host)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Ping inviato a {host.name}'})

# --- CRUD STANDARD ---
@app.route('/add', methods=['POST'])
def add_host():
    name = request.form.get('name')
    url = request.form.get('url')
    interval = request.form.get('interval')
    if name and url and interval:
        # Aggiungo http se manca
        if not url.startswith('http'):
            url = 'https://' + url
        new_host = Host(name=name, url=url, interval=int(interval))
        db.session.add(new_host)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_host(id):
    host = Host.query.get_or_404(id)
    db.session.delete(host)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/toggle/<int:id>')
def toggle_host(id):
    host = Host.query.get_or_404(id)
    host.active = not host.active
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['POST'])
def edit_host(id):
    host = Host.query.get_or_404(id)
    host.name = request.form.get('name')
    host.url = request.form.get('url')
    host.interval = int(request.form.get('interval'))
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)