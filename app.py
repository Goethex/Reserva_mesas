from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import copy

app = Flask(__name__)
app.secret_key = "restaurante_secreto"

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect('restaurant.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tables (
        id INTEGER PRIMARY KEY,
        number INTEGER,
        capacity INTEGER,
        location TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY,
        customer_name TEXT,
        customer_phone TEXT,
        table_id INTEGER,
        reservation_date TEXT,
        start_time TEXT,
        end_time TEXT,
        guests INTEGER,
        type TEXT,
        status TEXT,
        FOREIGN KEY (table_id) REFERENCES tables (id)
    )
    ''')
    
    # Verificar si ya hay mesas en la base de datos
    cursor.execute("SELECT COUNT(*) FROM tables")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Insertar algunas mesas de ejemplo
        tables = [
            (1, 4, 'Ventana'),
            (2, 2, 'Bar'),
            (3, 6, 'Jardin'),
            (4, 8, 'Area privada'),
            (5, 4, 'Area principal'),
        ]
        cursor.executemany("INSERT INTO tables (number, capacity, location) VALUES (?, ?, ?)", tables)
    
    conn.commit()
    conn.close()

def reset_db():
    conn = sqlite3.connect('restaurant.db')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS reservations")
    cursor.execute("DROP TABLE IF EXISTS tables")
    conn.commit()
    conn.close()
    init_db()

# Patrón Flyweight - Gestor de mesas
class TableManager:
    _tables = {}
    
    @staticmethod
    def get_table(table_id, number, capacity, location):
        key = f"{table_id}_{number}_{capacity}_{location}"
        if key not in TableManager._tables:
            TableManager._tables[key] = Table(table_id, number, capacity, location)
        return TableManager._tables[key]
    
    @staticmethod
    def get_all_tables():
        conn = sqlite3.connect('restaurant.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, number, capacity, location FROM tables")
        tables_data = cursor.fetchall()
        conn.close()
        
        tables = []
        for table_data in tables_data:
            table_id, number, capacity, location = table_data
            table = TableManager.get_table(table_id, number, capacity, location)
            tables.append(table)
        
        return tables
    
    @staticmethod
    def is_table_available(table_id, reservation_date, start_time, end_time):
        conn = sqlite3.connect('restaurant.db')
        cursor = conn.cursor()
        cursor.execute('''
        SELECT COUNT(*) FROM reservations
        WHERE table_id = ? 
        AND reservation_date = ?
        AND status = 'confirmed'
        AND (
            (? < end_time AND ? > start_time)
        )
        ''', (table_id, reservation_date, start_time, end_time))
        count = cursor.fetchone()[0]
        conn.close()
        print(f"Checking table {table_id} on {reservation_date} from {start_time} to {end_time}: {'available' if count == 0 else 'unavailable'}")
        return count == 0

# Clase Table para el patrón Flyweight
class Table:
    def __init__(self, table_id, number, capacity, location):
        self.id = table_id
        self.number = number
        self.capacity = capacity
        self.location = location
    
    def __str__(self):
        return f"Mesa #{self.number} (Capacidad: {self.capacity}, Ubicación: {self.location})"

# Patrón Abstract Factory - Fábricas de componentes del restaurante
class RestaurantComponentFactory:
    def create_table(self):
        pass
    
    def create_menu(self):
        pass
    
    def create_staff(self):
        pass

class StandardRestaurantFactory(RestaurantComponentFactory):
    def create_table(self, table_id, number, capacity, location):
        return TableManager.get_table(table_id, number, capacity, location)
    
    def create_menu(self):
        return StandardMenu()
    
    def create_staff(self):
        return StandardStaff()

class VIPRestaurantFactory(RestaurantComponentFactory):
    def create_table(self, table_id, number, capacity, location):
        table = TableManager.get_table(table_id, number, capacity, location)
        return table
    
    def create_menu(self):
        return VIPMenu()
    
    def create_staff(self):
        return VIPStaff()

# Clases de menú y personal para Abstract Factory
class Menu:
    def display(self):
        pass

class StandardMenu(Menu):
    def display(self):
        return "Menú Estándar"

class VIPMenu(Menu):
    def display(self):
        return "Menú VIP con opciones premium"

class Staff:
    def serve(self):
        pass

class StandardStaff(Staff):
    def serve(self):
        return "Servicio estándar"

class VIPStaff(Staff):
    def serve(self):
        return "Servicio VIP personalizado"

# Patrón Factory Method - Creación de diferentes tipos de reservas
class ReservationFactory:
    def create_reservation(self, customer_name, customer_phone, table_id, reservation_date, 
                          start_time, end_time, guests):
        pass

class StandardReservationFactory(ReservationFactory):
    def create_reservation(self, customer_name, customer_phone, table_id, reservation_date, 
                          start_time, end_time, guests):
        reservation = Reservation()
        reservation.customer_name = customer_name
        reservation.customer_phone = customer_phone
        reservation.table_id = table_id
        reservation.reservation_date = reservation_date
        reservation.start_time = start_time
        reservation.end_time = end_time
        reservation.guests = guests
        reservation.type = "standard"
        return reservation

class VIPReservationFactory(ReservationFactory):
    def create_reservation(self, customer_name, customer_phone, table_id, reservation_date, 
                          start_time, end_time, guests):
        reservation = Reservation()
        reservation.customer_name = customer_name
        reservation.customer_phone = customer_phone
        reservation.table_id = table_id
        reservation.reservation_date = reservation_date
        reservation.start_time = start_time
        reservation.end_time = end_time
        reservation.guests = guests
        reservation.type = "vip"
        return reservation

class GroupReservationFactory(ReservationFactory):
    def create_reservation(self, customer_name, customer_phone, table_id, reservation_date, 
                          start_time, end_time, guests):
        reservation = Reservation()
        reservation.customer_name = customer_name
        reservation.customer_phone = customer_phone
        reservation.table_id = table_id
        reservation.reservation_date = reservation_date
        reservation.start_time = start_time
        reservation.end_time = end_time
        reservation.guests = guests
        reservation.type = "group"
        return reservation

# Clase Reservation
class Reservation:
    def __init__(self):
        self.customer_name = None
        self.customer_phone = None
        self.table_id = None
        self.reservation_date = None
        self.start_time = None
        self.end_time = None
        self.guests = None
        self.type = None
        self.status = 'confirmed'
    
    def save(self):
        try:
            start_time = datetime.strptime(self.start_time, '%H:%M').strftime('%H:%M')
            end_time = datetime.strptime(self.end_time, '%H:%M').strftime('%H:%M')
        except ValueError:
            start_time = datetime.strptime(self.start_time, '%I:%M %p').strftime('%H:%M')
            end_time = datetime.strptime(self.end_time, '%I:%M %p').strftime('%H:%M')
        self.start_time, self.end_time = start_time, end_time
        
        if not TableManager.is_table_available(self.table_id, self.reservation_date, self.start_time, self.end_time):
            raise ValueError("Table is not available for the selected time slot")
        
        conn = sqlite3.connect('restaurant.db')
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO reservations 
        (customer_name, customer_phone, table_id, reservation_date, start_time, end_time, guests, type, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.customer_name, self.customer_phone, self.table_id, self.reservation_date, 
              self.start_time, self.end_time, self.guests, self.type, self.status))
        
        conn.commit()
        conn.close()
    
    def clone(self):
        return copy.deepcopy(self)

# Patrón Builder - Construcción paso a paso de reservas complejas
class ReservationBuilder:
    def __init__(self):
        self.reservation = Reservation()
    
    def set_customer_info(self, name, phone):
        self.reservation.customer_name = name
        self.reservation.customer_phone = phone
        return self
    
    def set_table(self, table_id):
        self.reservation.table_id = table_id
        return self
    
    def set_date_time(self, date, start_time, end_time):
        self.reservation.reservation_date = date
        self.reservation.start_time = start_time
        self.reservation.end_time = end_time
        return self
    
    def set_guests(self, guests):
        self.reservation.guests = guests
        return self
    
    def set_type(self, reservation_type):
        self.reservation.type = reservation_type
        return self
    
    def set_status(self, status):
        self.reservation.status = status
        return self
    
    def build(self):
        return self.reservation

# Rutas de Flask
@app.route('/')
def index():
    tables = TableManager.get_all_tables()
    return render_template('index.html', tables=tables)

@app.route('/tables')
def view_tables():
    tables = TableManager.get_all_tables()
    reservation_date = request.args.get('reservation_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    if reservation_date and start_time and end_time:
        if start_time >= end_time:
            flash('La hora de fin debe ser posterior a la hora de inicio.', 'error')
            tables_with_status = [
                {'id': table.id, 'number': table.number, 'capacity': table.capacity, 'location': table.location, 'status': None}
                for table in tables
            ]
        else:
            tables_with_status = []
            for table in tables:
                is_available = TableManager.is_table_available(table.id, reservation_date, start_time, end_time)
                tables_with_status.append({
                    'id': table.id,
                    'number': table.number,
                    'capacity': table.capacity,
                    'location': table.location,
                    'status': 'available' if is_available else 'reserved'
                })
            print(f"Tables for {reservation_date} {start_time}-{end_time}: {[t['id'] for t in tables_with_status if t['status'] == 'available']} available")
    else:
        tables_with_status = [
            {'id': table.id, 'number': table.number, 'capacity': table.capacity, 'location': table.location, 'status': None}
            for table in tables
        ]
    
    return render_template('tables.html', tables=tables_with_status, reservation_date=reservation_date, 
                         start_time=start_time, end_time=end_time, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/reservations')
def view_reservations():
    conn = sqlite3.connect('restaurant.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
    SELECT r.*, t.number as table_number 
    FROM reservations r 
    JOIN tables t ON r.table_id = t.id
    ORDER BY r.reservation_date, r.start_time
    ''')
    reservations = cursor.fetchall()
    conn.close()
    
    formatted_reservations = []
    for res in reservations:
        res_dict = dict(res)
        start_time = datetime.strptime(res['start_time'], '%H:%M')
        end_time = datetime.strptime(res['end_time'], '%H:%M')
        res_dict['start_time'] = start_time.strftime('%I:%M %p')
        res_dict['end_time'] = end_time.strftime('%I:%M %p')
        formatted_reservations.append(res_dict)
    
    return render_template('reservations.html', reservations=formatted_reservations)

@app.route('/new_reservation', methods=['GET', 'POST'])
def new_reservation():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_phone = request.form['customer_phone']
        table_id = int(request.form['table_id'])
        reservation_date = request.form['reservation_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        guests = int(request.form['guests'])
        reservation_type = request.form['reservation_type']
        
        # Validate time slot
        if start_time >= end_time:
            flash('La hora de fin debe ser posterior a la hora de inicio.', 'error')
            tables = TableManager.get_all_tables()
            return render_template('new_reservation.html', tables=tables, form_data=request.form)
        
        # Validate operating hours
        if start_time < '10:00' or end_time > '22:00':
            flash('Las reservas deben estar entre las 10:00 y las 22:00.', 'error')
            tables = TableManager.get_all_tables()
            return render_template('new_reservation.html', tables=tables, form_data=request.form)
        
        # Validate guests against table capacity
        conn = sqlite3.connect('restaurant.db')
        cursor = conn.cursor()
        cursor.execute("SELECT capacity FROM tables WHERE id = ?", (table_id,))
        table_capacity = cursor.fetchone()[0]
        conn.close()
        if guests > table_capacity:
            flash(f'El número de personas ({guests}) excede la capacidad de la mesa ({table_capacity}).', 'error')
            tables = TableManager.get_all_tables()
            return render_template('new_reservation.html', tables=tables, form_data=request.form)
        
        # Usar el patrón Builder para crear la reserva
        builder = ReservationBuilder()
        reservation = (builder
            .set_customer_info(customer_name, customer_phone)
            .set_table(table_id)
            .set_date_time(reservation_date, start_time, end_time)
            .set_guests(guests)
            .set_type(reservation_type)
            .build())
        
        try:
            reservation.save()
            flash('Reserva creada exitosamente!', 'success')
            return redirect(url_for('view_reservations'))
        except ValueError as e:
            flash(str(e), 'error')
            tables = TableManager.get_all_tables()
            print(f"Error saving reservation: {str(e)}")
            return render_template('new_reservation.html', tables=tables, form_data=request.form)
    
    # For GET requests, show available tables
    tables = TableManager.get_all_tables()
    reservation_date = request.args.get('reservation_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    table_id = request.args.get('table_id')
    
    if reservation_date and start_time and end_time:
        available_tables = [
            table for table in tables
            if TableManager.is_table_available(table.id, reservation_date, start_time, end_time)
        ]
        print(f"Available tables for {reservation_date} {start_time}-{end_time}: {[table.id for table in available_tables]}")
    else:
        available_tables = tables
    
    return render_template('new_reservation.html', tables=available_tables, 
                         form_data={
                             'reservation_date': reservation_date or '',
                             'start_time': start_time or '19:00',
                             'end_time': end_time or '21:00',
                             'table_id': table_id or ''
                         }, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/templates')
def view_templates():
    # Ejemplos de plantillas de reserva usando el patrón Prototype
    standard_template = Reservation()
    standard_template.start_time = "19:00"
    standard_template.end_time = "21:00"
    standard_template.guests = 2
    standard_template.type = "standard"
    
    vip_template = Reservation()
    vip_template.start_time = "20:00"
    vip_template.end_time = "22:00"
    vip_template.guests = 2
    vip_template.type = "vip"
    
    group_template = Reservation()
    group_template.start_time = "18:00"
    group_template.end_time = "21:00"
    group_template.guests = 8
    group_template.type = "group"
    
    templates = [standard_template, vip_template, group_template]
    return render_template('templates.html', templates=templates)

@app.route('/use_template/<template_type>', methods=['GET'])
def use_template(template_type):
    # Crear una plantilla base según el tipo
    if template_type == 'standard':
        template = Reservation()
        template.start_time = "19:00"
        template.end_time = "21:00"
        template.guests = 2
        template.type = "standard"
    elif template_type == 'vip':
        template = Reservation()
        template.start_time = "20:00"
        template.end_time = "22:00"
        template.guests = 2
        template.type = "vip"
    elif template_type == 'group':
        template = Reservation()
        template.start_time = "18:00"
        template.end_time = "21:00"
        template.guests = 8
        template.type = "group"
    else:
        flash('Tipo de plantilla no válido', 'error')
        return redirect(url_for('view_templates'))
    
    # Clonar la plantilla (Patrón Prototype)
    new_reservation = template.clone()
    
    # Formatear la fecha actual para el formulario
    today = datetime.now().strftime('%Y-%m-%d')
    
    tables = TableManager.get_all_tables()
    return render_template('new_reservation.html', 
                          tables=tables,
                          template=new_reservation,
                          today=today)

@app.route('/get_available_tables', methods=['GET'])
def get_available_tables():
    reservation_date = request.args.get('reservation_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    if not (reservation_date and start_time and end_time):
        print("Missing date/time parameters for get_available_tables")
        return jsonify({'tables': []})
    
    tables = TableManager.get_all_tables()
    available_tables = [
        {'id': table.id, 'number': table.number, 'capacity': table.capacity, 'location': table.location}
        for table in tables
        if TableManager.is_table_available(table.id, reservation_date, start_time, end_time)
    ]
    
    print(f"Returning {len(available_tables)} available tables for {reservation_date} {start_time}-{end_time}")
    return jsonify({'tables': available_tables})

@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
def cancel_reservation(reservation_id):
    conn = sqlite3.connect('restaurant.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE reservations SET status = 'cancelled' WHERE id = ?", (reservation_id,))
    conn.commit()
    conn.close()
    flash('Reserva cancelada exitosamente!', 'success')
    return redirect(url_for('view_reservations'))

@app.route('/edit_reservation/<int:reservation_id>', methods=['GET', 'POST'])
def edit_reservation(reservation_id):
    conn = sqlite3.connect('restaurant.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch the existing reservation
    cursor.execute('''
    SELECT r.*, t.capacity, t.number AS table_number
    FROM reservations r
    JOIN tables t ON r.table_id = t.id
    WHERE r.id = ?
    ''', (reservation_id,))
    reservation = cursor.fetchone()
    
    if not reservation:
        flash('Reserva no encontrada.', 'error')
        return redirect(url_for('view_reservations'))
    
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_phone = request.form['customer_phone']
        table_id = int(request.form['table_id'])
        reservation_date = request.form['reservation_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        guests = int(request.form['guests'])
        reservation_type = request.form['reservation_type']
        
        # Validate time slot
        if start_time >= end_time:
            flash('La hora de fin debe ser posterior a la hora de inicio.', 'error')
            tables = TableManager.get_all_tables()
            return render_template('new_reservation.html', tables=tables, form_data=request.form, editing=True, reservation_id=reservation_id)
        
        # Validate operating hours
        if start_time < '10:00' or end_time > '22:00':
            flash('Las reservas deben estar entre las 10:00 y las 22:00.', 'error')
            tables = TableManager.get_all_tables()
            return render_template('new_reservation.html', tables=tables, form_data=request.form, editing=True, reservation_id=reservation_id)
        
        # Validate guests against table capacity
        cursor.execute("SELECT capacity FROM tables WHERE id = ?", (table_id,))
        table_capacity = cursor.fetchone()[0]
        if guests > table_capacity:
            flash(f'El número de personas ({guests}) excede la capacidad de la mesa ({table_capacity}).', 'error')
            tables = TableManager.get_all_tables()
            return render_template('new_reservation.html', tables=tables, form_data=request.form, editing=True, reservation_id=reservation_id)
        
        # Check table availability, excluding the current reservation
        cursor.execute('''
        SELECT COUNT(*) FROM reservations
        WHERE table_id = ? 
        AND reservation_date = ?
        AND status = 'confirmed'
        AND id != ?
        AND (
            (? < end_time AND ? > start_time)
        )
        ''', (table_id, reservation_date, reservation_id, start_time, end_time))
        count = cursor.fetchone()[0]
        if count > 0:
            flash('La mesa no está disponible para el horario seleccionado.', 'error')
            tables = TableManager.get_all_tables()
            return render_template('new_reservation.html', tables=tables, form_data=request.form, editing=True, reservation_id=reservation_id)
        
        # Usar el patrón Builder para actualizar la reserva
        builder = ReservationBuilder()
        updated_reservation = (builder
            .set_customer_info(customer_name, customer_phone)
            .set_table(table_id)
            .set_date_time(reservation_date, start_time, end_time)
            .set_guests(guests)
            .set_type(reservation_type)
            .set_status('confirmed')
            .build())
        
        try:
            # Actualizar la reserva en la base de datos
            cursor.execute('''
            UPDATE reservations
            SET customer_name = ?, customer_phone = ?, table_id = ?, reservation_date = ?,
                start_time = ?, end_time = ?, guests = ?, type = ?, status = ?
            WHERE id = ?
            ''', (customer_name, customer_phone, table_id, reservation_date, start_time, end_time,
                  guests, reservation_type, 'confirmed', reservation_id))
            conn.commit()
            flash('Reserva actualizada exitosamente!', 'success')
            return redirect(url_for('view_reservations'))
        except Exception as e:
            conn.rollback()
            flash(f'Error al actualizar la reserva: {str(e)}', 'error')
            tables = TableManager.get_all_tables()
            print(f"Error updating reservation: {str(e)}")
            return render_template('new_reservation.html', tables=tables, form_data=request.form, editing=True, reservation_id=reservation_id)
        finally:
            conn.close()
    
    # For GET requests, pre-fill the form with existing reservation data
    tables = TableManager.get_all_tables()
    form_data = {
        'customer_name': reservation['customer_name'],
        'customer_phone': reservation['customer_phone'],
        'table_id': str(reservation['table_id']),
        'reservation_date': reservation['reservation_date'],
        'start_time': reservation['start_time'],
        'end_time': reservation['end_time'],
        'guests': str(reservation['guests']),
        'reservation_type': reservation['type']
    }
    conn.close()
    return render_template('new_reservation.html', tables=tables, form_data=form_data, editing=True, reservation_id=reservation_id)

@app.route('/debug_reservations')
def debug_reservations():
    conn = sqlite3.connect('restaurant.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservations ORDER BY reservation_date, start_time")
    reservations = cursor.fetchall()
    conn.close()
    return render_template('reservations.html', reservations=reservations)

if __name__ == '__main__':
    init_db()       #Comentar la primera vez que se eejecute
    # reset_db()      #Comentar cuando ya se realizo la primera visita
    app.run(debug=True)