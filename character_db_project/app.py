from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///characters.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # needed for flashing messages
db = SQLAlchemy(app)

logging.basicConfig(level=logging.DEBUG)

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    arcs = db.relationship('CharacterArc', backref='character', lazy=True)
    relationships_from = db.relationship('Relationship', foreign_keys='Relationship.character_from_id', backref='character_from', lazy=True)
    relationships_to = db.relationship('Relationship', foreign_keys='Relationship.character_to_id', backref='character_to', lazy=True)

class CharacterArc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    act1_self_esteem = db.Column(db.Float)
    act1_social_reputation = db.Column(db.Float)
    act2_self_esteem = db.Column(db.Float)
    act2_social_reputation = db.Column(db.Float)
    act3_self_esteem = db.Column(db.Float)
    act3_social_reputation = db.Column(db.Float)

    @hybrid_property
    def act1_psychological_index(self):
        return self.act1_self_esteem - self.act1_social_reputation

    @hybrid_property
    def act2_psychological_index(self):
        return self.act2_self_esteem - self.act2_social_reputation

    @hybrid_property
    def act3_psychological_index(self):
        return self.act3_self_esteem - self.act3_social_reputation

class Relationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_from_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    character_to_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    relationship_type = db.Column(db.String(50), nullable=False)
    intensity = db.Column(db.Integer, nullable=False)  # Scale from 1 to 10

@app.route('/')
def index():
    characters = Character.query.all()
    return render_template('index.html', characters=characters)

@app.route('/add', methods=['POST'])
def add_character():
    name = request.form['name']
    description = request.form['description']
    new_character = Character(name=name, description=description)
    db.session.add(new_character)
    db.session.commit()
    flash('Character added successfully!')
    return redirect(url_for('index'))

@app.route('/character/<int:id>')
def character_detail(id):
    character = Character.query.get_or_404(id)
    arc = CharacterArc.query.filter_by(character_id=id).first()
    relationships = Relationship.query.filter((Relationship.character_from_id == id) | (Relationship.character_to_id == id)).all()
    characters = Character.query.all()
    return render_template('character_detail.html', character=character, arc=arc, relationships=relationships, characters=characters)

@app.route('/character/<int:id>/edit', methods=['GET', 'POST'])
def edit_character(id):
    character = Character.query.get_or_404(id)
    if request.method == 'POST':
        character.name = request.form['name']
        character.description = request.form['description']
        db.session.commit()
        flash('Character updated successfully!')
        return redirect(url_for('character_detail', id=character.id))
    return render_template('edit_character.html', character=character)

@app.route('/character/<int:id>/delete', methods=['POST'])
def delete_character(id):
    character = Character.query.get_or_404(id)
    db.session.delete(character)
    db.session.commit()
    flash('Character deleted successfully!')
    return redirect(url_for('index'))

@app.route('/character/<int:id>/add_arc', methods=['POST'])
def add_character_arc(id):
    character = Character.query.get_or_404(id)
    existing_arc = CharacterArc.query.filter_by(character_id=id).first()
    if existing_arc:
        flash('Character arc already exists. Use edit function to modify.')
        return redirect(url_for('character_detail', id=id))
    
    new_arc = CharacterArc(
        character_id=id,
        act1_self_esteem=float(request.form['act1_self_esteem']),
        act1_social_reputation=float(request.form['act1_social_reputation']),
        act2_self_esteem=float(request.form['act2_self_esteem']),
        act2_social_reputation=float(request.form['act2_social_reputation']),
        act3_self_esteem=float(request.form['act3_self_esteem']),
        act3_social_reputation=float(request.form['act3_social_reputation'])
    )
    db.session.add(new_arc)
    db.session.commit()
    flash('Character arc added successfully!')
    return redirect(url_for('character_detail', id=id))

@app.route('/character/<int:id>/edit_arc', methods=['POST'])
def edit_character_arc(id):
    character = Character.query.get_or_404(id)
    arc = CharacterArc.query.filter_by(character_id=id).first()
    if arc:
        arc.act1_self_esteem = float(request.form['act1_self_esteem'])
        arc.act1_social_reputation = float(request.form['act1_social_reputation'])
        arc.act2_self_esteem = float(request.form['act2_self_esteem'])
        arc.act2_social_reputation = float(request.form['act2_social_reputation'])
        arc.act3_self_esteem = float(request.form['act3_self_esteem'])
        arc.act3_social_reputation = float(request.form['act3_social_reputation'])
        db.session.commit()
        flash('Character arc updated successfully!')
    else:
        flash('Character arc not found!')
    return redirect(url_for('character_detail', id=id))

@app.route('/character/<int:id>/arc_data')
def character_arc_data(id):
    character = Character.query.get_or_404(id)
    arc = CharacterArc.query.filter_by(character_id=id).first()
    if arc:
        data = {
            'labels': ['Act 1', 'Act 2', 'Act 3'],
            'psychological_index': [
                arc.act1_psychological_index,
                arc.act2_psychological_index,
                arc.act3_psychological_index
            ]
        }
        return jsonify(data)
    return jsonify({'error': 'No arc data available'})

@app.route('/character/<int:id>/add_relationship', methods=['POST'])
def add_relationship(id):
    character_from = Character.query.get_or_404(id)
    character_to_id = request.form['character_to_id']
    relationship_type = request.form['relationship_type']
    intensity = int(request.form['intensity'])

    new_relationship = Relationship(
        character_from_id=id,
        character_to_id=character_to_id,
        relationship_type=relationship_type,
        intensity=intensity
    )
    db.session.add(new_relationship)
    db.session.commit()
    flash('Relationship added successfully!')
    return redirect(url_for('character_detail', id=id))

@app.route('/compare_characters')
def compare_characters():
    characters = Character.query.all()
    return render_template('compare_characters.html', characters=characters)

@app.route('/how_to_use')
def how_to_use():
    return render_template('how_to_use.html')

@app.route('/compare_characters_data', methods=['POST'])
def compare_characters_data():
    character_ids = request.json['character_ids']
    data = []
    for id in character_ids:
        character = Character.query.get(id)
        arc = CharacterArc.query.filter_by(character_id=id).first()
        if character and arc:
            data.append({
                'name': character.name,
                'psychological_index': [
                    arc.act1_psychological_index,
                    arc.act2_psychological_index,
                    arc.act3_psychological_index
                ]
            })
    return jsonify({
        'labels': ['Act 1', 'Act 2', 'Act 3'],
        'datasets': data
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.logger.info('Starting the Flask application')
    app.run(debug=True, host='0.0.0.0', port=5004)
