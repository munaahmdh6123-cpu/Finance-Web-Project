from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rahasia-super-aman-123')

database_url = os.environ.get('DATABASE_URL', 'sqlite:///keuangan.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

db = SQLAlchemy(app)


# ================= MODEL DATABASE =================
class Transaksi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    keterangan = db.Column(db.String(200), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    jenis = db.Column(db.String(10), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Transaksi {self.keterangan}>'


# ================= ROUTES =================
@app.route('/')
def index():
    transaksi = Transaksi.query.order_by(Transaksi.tanggal.desc()).all()
    total_masuk = sum(t.jumlah for t in transaksi if t.jenis == 'masuk')
    total_keluar = sum(t.jumlah for t in transaksi if t.jenis == 'keluar')
    saldo = total_masuk - total_keluar
    return render_template('index.html',
                           transaksi=transaksi,
                           total_masuk=total_masuk,
                           total_keluar=total_keluar,
                           saldo=saldo)


@app.route('/tambah', methods=['GET', 'POST'])
def tambah():
    if request.method == 'POST':
        tanggal_str = request.form['tanggal']
        transaksi_baru = Transaksi(
            tanggal=datetime.strptime(tanggal_str, '%Y-%m-%d').date(),
            keterangan=request.form['keterangan'],
            kategori=request.form['kategori'],
            jenis=request.form['jenis'],
            jumlah=float(request.form['jumlah'])
        )
        db.session.add(transaksi_baru)
        db.session.commit()
        flash('Transaksi berhasil ditambahkan!', 'success')
        return redirect(url_for('index'))
    return render_template('tambah.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    transaksi = Transaksi.query.get_or_404(id)
    if request.method == 'POST':
        transaksi.tanggal = datetime.strptime(request.form['tanggal'], '%Y-%m-%d').date()
        transaksi.keterangan = request.form['keterangan']
        transaksi.kategori = request.form['kategori']
        transaksi.jenis = request.form['jenis']
        transaksi.jumlah = float(request.form['jumlah'])
        db.session.commit()
        flash('Transaksi berhasil diupdate!', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', transaksi=transaksi)


@app.route('/hapus/<int:id>')
def hapus(id):
    transaksi = Transaksi.query.get_or_404(id)
    db.session.delete(transaksi)
    db.session.commit()
    flash('Transaksi berhasil dihapus!', 'success')
    return redirect(url_for('index'))


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)