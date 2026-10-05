
import json
import os
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Instala reportlab: pip install reportlab==3.6.13")

DATA_FILE = "datos.json"

class Producto:
    def __init__(self, id, nombre, costo, precio_venta, stock):
        self.id = id
        self.nombre = nombre
        self.costo = float(costo)
        self.precio_venta = float(precio_venta)
        self.stock = int(stock)
    
    def ganancia_unitaria(self):
        return self.precio_venta - self.costo
    
    def margen(self):
        return (self.ganancia_unitaria() / self.precio_venta * 100) if self.precio_venta else 0

    def to_dict(self):
        return self.__dict__

class Venta:
    def __init__(self, id_venta, fecha, items):
        self.id_venta = id_venta
        self.fecha = fecha
        self.items = items
        self.total = sum(i["producto"].precio_venta * i["cantidad"] for i in items)
        self.costo_total = sum(i["producto"].costo * i["cantidad"] for i in items)
        self.ganancia = self.total - self.costo_total

class SistemaVentas:
    def __init__(self):
        self.productos = {}
        self.ventas = []
        self.cargar_datos()

    def agregar_producto(self, id, nombre, costo, precio_venta, stock):
        if id in self.productos:
            print(f"El producto {id} ya existe.")
            return
        self.productos[id] = Producto(id, nombre, costo, precio_venta, stock)
        self.guardar_datos()
        print(f"Producto {nombre} agregado.")

    def borrar_producto(self, id_producto):
        if id_producto not in self.productos:
            print(f"Producto {id_producto} no existe")
            return
        nombre = self.productos[id_producto].nombre
        del self.productos[id_producto]
        self.guardar_datos()
        print(f"Producto {nombre} ({id_producto}) borrado correctamente.")

    def editar_producto(self, id_producto):
        if id_producto not in self.productos:
            print(f"Producto {id_producto} no existe")
            return
        p = self.productos[id_producto]
        print(f"\nEditando {p.nombre} (Enter para dejar igual)")
        nuevo_nombre = input(f"Nombre [{p.nombre}]: ").strip()
        nuevo_costo = input(f"Costo [{p.costo}]: ").strip()
        nuevo_precio = input(f"Precio venta [{p.precio_venta}]: ").strip()
        nuevo_stock = input(f"Stock [{p.stock}]: ").strip()

        if nuevo_nombre:
            p.nombre = nuevo_nombre
        if nuevo_costo:
            try: p.costo = float(nuevo_costo)
            except: pass
        if nuevo_precio:
            try: p.precio_venta = float(nuevo_precio)
            except: pass
        if nuevo_stock:
            try: p.stock = int(nuevo_stock)
            except: pass

        self.guardar_datos()
        print(f"Producto {id_producto} actualizado.")

    def listar_productos(self):
        print("\n--- INVENTARIO ---")
        for p in self.productos.values():
            print(f"{p.id} | {p.nombre} | Costo: S/{p.costo} | Venta: S/{p.precio_venta} | Stock: {p.stock} | Margen: {p.margen():.1f}%")

    def vender(self, items_dict):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items_venta = []
        for pid, cant in items_dict.items():
            if pid not in self.productos:
                print(f"Producto {pid} no existe")
                return None
            prod = self.productos[pid]
            if prod.stock < cant:
                print(f"Stock insuficiente para {prod.nombre} (stock: {prod.stock})")
                return None
            items_venta.append({"producto": prod, "cantidad": cant})
        
        for item in items_venta:
            item["producto"].stock -= item["cantidad"]
        
        id_venta = len(self.ventas) + 1
        venta = Venta(id_venta, fecha, items_venta)
        self.ventas.append(venta)
        self.guardar_datos()
        print(f"\nVenta #{id_venta} registrada - Total: S/{venta.total:.2f} | Ganancia: S/{venta.ganancia:.2f}")
        return venta

    def resumen(self):
        total_ventas = sum(v.total for v in self.ventas)
        total_costos = sum(v.costo_total for v in self.ventas)
        total_ganancia = total_ventas - total_costos
        print("\n--- RESUMEN FINANCIERO ---")
        print(f"Total ventas: S/{total_ventas:.2f}")
        print(f"Total costos: S/{total_costos:.2f}")
        print(f"Ganancia neta: S/{total_ganancia:.2f}")
        return total_ventas, total_costos, total_ganancia

    
    def generar_reporte_pdf(self, nombre_archivo="reporte_ventas.pdf"):
        if not PDF_AVAILABLE:
            print("Instala reportlab primero")
            return
        doc = SimpleDocTemplate(nombre_archivo, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph(f"<b>Sistema de Ventas - Reporte</b><br/>Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Title']))
        story.append(Spacer(1, 20))

        total_ventas = sum(v.total for v in self.ventas)
        total_costos = sum(v.costo_total for v in self.ventas)
        total_ganancia = total_ventas - total_costos

        resumen_data = [
            ["Concepto", "Monto"],
            ["Total Ventas", f"S/ {total_ventas:.2f}"],
            ["Total Costos", f"S/ {total_costos:.2f}"],
            ["Ganancia Neta", f"S/ {total_ganancia:.2f}"],
            ["N° Ventas", str(len(self.ventas))]
        ]
        t = Table(resumen_data, colWidths=[200, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        story.append(Paragraph("<b>Detalle de Ventas</b>", styles['Heading2']))
        ventas_data = [["ID", "Fecha", "Productos", "Total", "Ganancia"]]
        for v in self.ventas:
            prod_str = ", ".join([f"{i['producto'].nombre} x{i['cantidad']}" for i in v.items])
            ventas_data.append([str(v.id_venta), v.fecha, prod_str[:40], f"S/ {v.total:.2f}", f"S/ {v.ganancia:.2f}"])
        if len(ventas_data)==1:
            ventas_data.append(["-", "-", "Sin ventas", "-", "-"])
        t2 = Table(ventas_data, colWidths=[30, 110, 170, 60, 60])
        t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
        story.append(t2)
        doc.build(story)
        ruta = os.path.abspath(nombre_archivo)
        print(f"PDF generado: {ruta}")
        try:
            imprimir = input("¿Deseas IMPRIMIR ahora? (s/n): ").lower()
            if imprimir == "s":
                if os.name == "nt":
                    os.startfile(ruta, "print")
                    print("Enviando a la impresora...")
                else:
                    print(f"Abre el archivo para imprimir: {ruta}")
        except Exception as e:
            print(f"No se pudo enviar a imprimir automaticamente: {e}")
            print(f"Abre el PDF manualmente: {ruta} y presiona Ctrl+P")


    def guardar_datos(self):
        data = {
            "productos": {k: v.to_dict() for k, v in self.productos.items()},
            "ventas": [{"id_venta": v.id_venta, "fecha": v.fecha, "items": [{"id_producto": i["producto"].id, "cantidad": i["cantidad"]} for i in v.items]} for v in self.ventas]
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def cargar_datos(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            for pid, pd in data.get("productos", {}).items():
                self.productos[pid] = Producto(**pd)
            for vd in data.get("ventas", []):
                items = []
                for it in vd["items"]:
                    if it["id_producto"] in self.productos:
                        items.append({"producto": self.productos[it["id_producto"]], "cantidad": it["cantidad"]})
                if items:
                    v = Venta(vd["id_venta"], vd["fecha"], items)
                    self.ventas.append(v)
        except:
            pass

if __name__ == "__main__":
    s = SistemaVentas()
    if not s.productos:
        s.agregar_producto("P001", "Laptop HP", 1800, 2500, 10)
        s.agregar_producto("P002", "Mouse Logitech", 35, 70, 50)
        s.agregar_producto("P003", "Teclado Mecanico", 90, 160, 30)
        s.agregar_producto("P004", "Monitor 24", 320, 480, 15)

    while True:
        print("\n" + "="*40)
        print(" SISTEMA DE VENTAS - MENU")
        print("="*40)
        print("1. Listar productos")
        print("2. Agregar producto")
        print("3. Vender")
        print("4. Ver resumen / ganancia")
        print("5. Generar reporte PDF")
        print("6. Borrar producto")
        print("7. Editar producto")
        print("8. Salir")
        op = input("Elige opcion: ")

        if op == "1":
            s.listar_productos()
        elif op == "2":
            pid = input("ID: ")
            nom = input("Nombre: ")
            costo = float(input("Costo: "))
            venta = float(input("Precio venta: "))
            stock = int(input("Stock: "))
            s.agregar_producto(pid, nom, costo, venta, stock)
        elif op == "3":
            s.listar_productos()
            items = {}
            while True:
                pid = input("ID producto a vender (enter para terminar): ")
                if not pid: break
                cant = int(input(f"Cantidad de {pid}: "))
                items[pid] = cant
            if items:
                s.vender(items)
        elif op == "4":
            s.resumen()
        elif op == "5":
            s.generar_reporte_pdf("reporte_ventas.pdf")
        elif op == "6":
            s.listar_productos()
            pid = input("ID del producto a borrar: ").strip()
            if pid:
                conf = input(f"Seguro que quieres borrar {pid}? (s/n): ").lower()
                if conf == "s":
                    s.borrar_producto(pid)
        elif op == "7":
            s.listar_productos()
            pid = input("ID del producto a editar: ").strip()
            if pid:
                s.editar_producto(pid)
        elif op == "8":
            break
