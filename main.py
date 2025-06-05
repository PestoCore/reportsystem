from typing import Union

from fastapi import FastAPI, HTTPException, Depends, WebSocket
from sqlalchemy.orm import Session
from shapely import wkb, wkt
from fastapi.encoders import jsonable_encoder
from fastapi.websockets import WebSocketDisconnect
from models import Report, ReportCreate, StatusUpdate, LocationUpdate
from db_config import ORMBaseModel, db_engine, get_db_session
from encoders import to_dict
from datetime import datetime
import json

# niestety
import time
time.sleep(15)

ORMBaseModel.metadata.create_all(bind=db_engine)
app = FastAPI()

# websockety
@app.websocket("/ws/status_category_id")
async def positions(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Utrzymanie połączenia
    except WebSocketDisconnect:
        active_connections.remove(websocket)

active_connections: list[WebSocket] = []

# POST

@app.post("/report", status_code=201)
def create_report(report_create: ReportCreate, db_session: Session = Depends(get_db_session)):
    try:
        position_geom = wkt.loads(report_create.report_location)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid position WKT format")
    if not( 1 <= report_create.report_category_id <= 12 ):
        raise HTTPException(status_code=400, detail="Value of report_category_id out of range(1-12)")
    if not( 1 <= report_create.status_category_id <= 4 ):
        raise HTTPException(status_code=400, detail="Value of status_category_id out of range(1-4)")
    new_report = Report(
        report_category_id=report_create.report_category_id,
        description=report_create.description,
        time_of_submission=datetime.now(),
        status_category_id=report_create.status_category_id,
        report_location=f"SRID=2180;{report_create.report_location}"
    )
    db_session.add(new_report)
    db_session.commit()
    db_session.refresh(new_report)
    return jsonable_encoder({
        "id": new_report.id,
        "report_category_id": new_report.report_category_id,
        "description": new_report.description,
        "report_location": {
            "x": position_geom.x,
            "y": position_geom.y
        },
        "time_of_submission": new_report.time_of_submission,
        "status_category_id": new_report.status_category_id
    })

# GET

@app.get("/")
def test():
    return {"msg": "Jeśli to widać, działa :3"}

@app.get("/report")
def get_all_reports(db_session: Session = Depends(get_db_session)):
    reports = db_session.query(Report).all()
    result = []
    for report in reports:
        report_dict = to_dict(report)
        if report.report_location:
            position_geom = wkb.loads(bytes(report.report_location.data))
            report_dict['report_location'] = {
                "x": position_geom.x,
                "y": position_geom.y
            }
        result.append(report_dict)
    return jsonable_encoder(result)

@app.get("/report/{report_id}")
def get_report(report_id: int, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.report_location:
        raise HTTPException(status_code=404, detail="Position not available")
    position_geom = wkb.loads(bytes(report.report_location.data))
    return jsonable_encoder({
        "id": report.id,
        "report_category_id": report.report_category_id,
        "description": report.description,
        "report_location": {
            "x": position_geom.x,
            "y": position_geom.y
        },
        "time_of_submission": report.time_of_submission,
        "status_category_id": report.status_category_id
    })

@app.get("/report/{report_id}/report_location")
def get_report_location(report_id: int, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.report_location:
        raise HTTPException(status_code=404, detail="Position not available")
    position_geom = wkb.loads(bytes(report.report_location.data))
    return jsonable_encoder({
        "position": {
            "x": position_geom.x,
            "y": position_geom.y
        }
    })

@app.get("/report/{report_id}/status_category_id")
def get_report_location(report_id: int, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.report_location:
        raise HTTPException(status_code=404, detail="Position not available")
    position_geom = wkb.loads(bytes(report.report_location.data))
    return jsonable_encoder({
        "status_category_id": report.status_category_id
    })

# PUT

@app.put("/report/{report_id}/status_category_id")
async def update_status(report_id: int, status_update: StatusUpdate, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not( 1 <= status_update.status_category_id <= 4 ):
        raise HTTPException(status_code=400, detail="Value of status_category_id out of range(1-4)")
    report.status_category_id = status_update.status_category_id
    db_session.commit()
    db_session.refresh(report)
    # position_geom = wkb.loads(bytes(report.report_location.data))
    geom = wkb.loads(bytes(report.report_location.data))
    message = json.dumps({
        "id": report.id,
        "report_category_id": report.report_category_id,
        "description": report.description,
        "report_location": {
            "x": geom.x,
            "y": geom.y
        },
        "time_of_submission": report.time_of_submission.isoformat(),
        "status_category_id": report.status_category_id
    })
    for connection in active_connections:
        await connection.send_text(message)
    return jsonable_encoder({
        "message": "Status updated",
        "id": report.id,
        "status_category_id": status_update.status_category_id
    })

@app.put("/report/{report_id}/report_location")
async def update_status(report_id: int, location_update: LocationUpdate, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        position_geom = wkt.loads(location_update.report_location)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid position WKT format")
    report.report_location = location_update.report_location
    db_session.commit()
    db_session.refresh(report)
    geom = wkb.loads(bytes(report.report_location.data))
    message = json.dumps({
        "id": report.id,
        "report_category_id": report.report_category_id,
        "description": report.description,
        "report_location": {
            "x": geom.x,
            "y": geom.y
        },
        "time_of_submission": report.time_of_submission.isoformat(),
        "status_category_id": report.status_category_id
    })
    for connection in active_connections:
        await connection.send_text(message)
    return jsonable_encoder({
        "message": "Location updated",
        "id": report.id,
        "report_location": {
            "x": geom.x,
            "y": geom.y
        }
    })

# DELETE

@app.delete("/report/{report_id}")
def delete_report(report_id: int, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db_session.delete(report)
    db_session.commit()
    return jsonable_encoder({"message": "Report deleted"})
