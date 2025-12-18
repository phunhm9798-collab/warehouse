from flask import Blueprint, render_template, request, jsonify
from models import db
from models.location import Location

locations_bp = Blueprint('locations', __name__, url_prefix='/locations')

@locations_bp.route('/')
def index():
    return render_template('locations.html')

@locations_bp.route('/api/locations')
def get_locations():
    zone = request.args.get('zone', '')
    zone_type = request.args.get('zone_type', '')
    is_active = request.args.get('is_active')
    
    query = Location.query
    if zone:
        query = query.filter_by(zone=zone)
    if zone_type:
        query = query.filter_by(zone_type=zone_type)
    if is_active:
        query = query.filter_by(is_active=is_active.lower() == 'true')
    
    locations = query.order_by(Location.zone, Location.aisle, Location.rack, Location.shelf).all()
    return jsonify([l.to_dict() for l in locations])

@locations_bp.route('/api/locations/<int:location_id>')
def get_location(location_id):
    location = Location.query.get_or_404(location_id)
    return jsonify(location.to_dict())

@locations_bp.route('/api/locations', methods=['POST'])
def create_location():
    data = request.get_json()
    location = Location(
        zone=data['zone'],
        aisle=data['aisle'],
        rack=data['rack'],
        shelf=data['shelf'],
        bin=data.get('bin', '01'),
        max_capacity=data.get('max_capacity', 100),
        zone_type=data.get('zone_type', 'storage'),
        is_active=data.get('is_active', True)
    )
    db.session.add(location)
    db.session.commit()
    return jsonify(location.to_dict()), 201

@locations_bp.route('/api/locations/<int:location_id>', methods=['PUT'])
def update_location(location_id):
    location = Location.query.get_or_404(location_id)
    data = request.get_json()
    location.zone = data.get('zone', location.zone)
    location.aisle = data.get('aisle', location.aisle)
    location.rack = data.get('rack', location.rack)
    location.shelf = data.get('shelf', location.shelf)
    location.bin = data.get('bin', location.bin)
    location.max_capacity = data.get('max_capacity', location.max_capacity)
    location.zone_type = data.get('zone_type', location.zone_type)
    location.is_active = data.get('is_active', location.is_active)
    db.session.commit()
    return jsonify(location.to_dict())

@locations_bp.route('/api/locations/<int:location_id>', methods=['DELETE'])
def delete_location(location_id):
    location = Location.query.get(location_id)
    if location:
        db.session.delete(location)
        db.session.commit()
    return jsonify({'message': 'Deleted'})

@locations_bp.route('/api/locations/zones')
def get_zones():
    zones = db.session.query(Location.zone).distinct().order_by(Location.zone).all()
    return jsonify([z[0] for z in zones])

@locations_bp.route('/api/locations/zone-types')
def get_zone_types():
    return jsonify(['receiving', 'storage', 'shipping', 'staging', 'quarantine'])

@locations_bp.route('/api/locations/bulk', methods=['POST'])
def create_bulk_locations():
    data = request.get_json()
    zone = data['zone']
    zone_type = data.get('zone_type', 'storage')
    aisle_start = int(data.get('aisle_start', 1))
    aisle_end = int(data.get('aisle_end', 1))
    rack_start = int(data.get('rack_start', 1))
    rack_end = int(data.get('rack_end', 1))
    shelves = data.get('shelves', ['A', 'B', 'C'])
    max_capacity = data.get('max_capacity', 100)
    
    created = 0
    for aisle in range(aisle_start, aisle_end + 1):
        for rack in range(rack_start, rack_end + 1):
            for shelf in shelves:
                loc = Location(
                    zone=zone,
                    aisle=f'{aisle:02d}',
                    rack=f'{rack:02d}',
                    shelf=shelf,
                    bin='01',
                    max_capacity=max_capacity,
                    zone_type=zone_type
                )
                db.session.add(loc)
                created += 1
    
    db.session.commit()
    return jsonify({'message': f'Created {created} locations'}), 201
