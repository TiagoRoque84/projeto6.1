# blueprints/fleet/routes.py
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import fleet_bp
from models import db, Vehicle, MaintenanceLog, VehicleDocument
from forms import VehicleForm, MaintenanceLogForm, VehicleDocumentForm
from datetime import date
from dateutil.relativedelta import relativedelta
from utils import save_file 
import os
from flask import current_app

@fleet_bp.route('/')
@login_required
def list():
    vehicles = Vehicle.query.order_by(Vehicle.nome).all()
    return render_template('fleet/list.html', items=vehicles)

@fleet_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def new():
    form = VehicleForm()
    if form.validate_on_submit():
        new_vehicle = Vehicle()
        form.populate_obj(new_vehicle)
        db.session.add(new_vehicle)
        db.session.commit()
        flash('Veículo cadastrado com sucesso!', 'success')
        return redirect(url_for('fleet.list'))
    return render_template('fleet/form.html', form=form, title='Novo Veículo')

@fleet_bp.route('/<int:vehicle_id>/editar', methods=['GET', 'POST'])
@login_required
def edit(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    form = VehicleForm(obj=vehicle)
    if form.validate_on_submit():
        form.populate_obj(vehicle)
        db.session.commit()
        flash('Veículo atualizado com sucesso!', 'success')
        return redirect(url_for('fleet.list'))
    return render_template('fleet/form.html', form=form, title='Editar Veículo', item=vehicle)

@fleet_bp.route('/<int:vehicle_id>/ficha', methods=['GET', 'POST'])
@login_required
def details(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    form = MaintenanceLogForm()
    
    if form.validate_on_submit():
        new_log = MaintenanceLog(vehicle_id=vehicle.id)
        form.populate_obj(new_log)
        
        if new_log.tipo_servico.lower().strip() == 'troca de óleo':
            if new_log.km_atual:
                new_log.km_proxima_troca = new_log.km_atual + 5000
            if new_log.data:
                new_log.data_proxima_troca = new_log.data + relativedelta(months=6)

        db.session.add(new_log)
        db.session.commit()
        flash('Novo histórico de manutenção adicionado!', 'success')
        return redirect(url_for('fleet.details', vehicle_id=vehicle.id))
    
    oil_changes = vehicle.manutencoes.filter(MaintenanceLog.tipo_servico.ilike('%óleo%')).all()
    other_maintenances = vehicle.manutencoes.filter(~MaintenanceLog.tipo_servico.ilike('%óleo%')).all()
    
    return render_template('fleet/details.html', 
                           vehicle=vehicle, 
                           form=form,
                           oil_changes=oil_changes,
                           other_maintenances=other_maintenances)

@fleet_bp.route('/<int:vehicle_id>/docs', methods=["GET", "POST"])
@login_required
def docs(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    form = VehicleDocumentForm()
    if form.validate_on_submit():
        if form.arquivo.data:
            path = save_file(form.arquivo.data, "vehicle_docs")
            if path:
                doc = VehicleDocument(
                    vehicle_id=vehicle.id,
                    tipo=form.tipo.data,
                    descricao=form.descricao.data,
                    arquivo_path=path
                )
                db.session.add(doc)
                db.session.commit()
                flash("Documento do veículo enviado.", "success")
        else:
            flash("Nenhum arquivo selecionado.", "danger")
        return redirect(url_for('fleet.docs', vehicle_id=vehicle.id))

    documents = vehicle.documentos.order_by(VehicleDocument.uploaded_at.desc()).all()
    return render_template('fleet/docs.html', vehicle=vehicle, form=form, documents=documents)


@fleet_bp.route('/docs/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete_doc(doc_id):
    doc = VehicleDocument.query.get_or_404(doc_id)
    vehicle_id = doc.vehicle_id
    try:
        if doc.arquivo_path:
            full_path = os.path.join(current_app.root_path, "uploads", doc.arquivo_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        db.session.delete(doc)
        db.session.commit()
        flash("Documento do veículo excluído.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir documento: {e}", "danger")
    return redirect(url_for('fleet.docs', vehicle_id=vehicle_id))

# --- FUNÇÃO DE EXCLUIR VEÍCULO ADICIONADA AQUI ---
@fleet_bp.route('/<int:vehicle_id>/excluir', methods=['POST'])
@login_required
def delete(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    try:
        # A exclusão dos documentos e manutenções agora é automática por causa do "cascade" no models.py
        db.session.delete(vehicle)
        db.session.commit()
        flash('Veículo e todos os seus registros foram excluídos com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir o veículo: {e}', 'danger')
    return redirect(url_for('fleet.list'))