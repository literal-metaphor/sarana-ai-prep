from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
from thing_controller import ThingController
import json

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()
thing_controller = ThingController()

@app.get("/hello/{name}")
async def hello(name: str):
    return {
        "message": f"Hello {' '.join(word.capitalize() for word in name.split())}!"
    }

@app.get("/", response_model=List[dict])
async def get_things():
    """Get all things"""
    try:
        things = thing_controller.index()
        logger.info("Retrieved all things")
        return [thing.model_dump() for thing in things]
    except Exception as e:
        logger.error(f"Error getting things: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{id}", response_model=dict)
async def get_thing(id: str):
    """Get a single thing by ID"""
    try:
        thing = thing_controller.show(id)
        if not thing:
            logger.warning(f"Thing not found with ID: {id}")
            raise HTTPException(status_code=404, detail="Thing not found")
        logger.info(f"Retrieved thing with ID: {id}")
        return thing.model_dump()
    except Exception as e:
        logger.error(f"Error getting thing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/", response_model=dict, status_code=201)
async def create_thing(thing: dict):
    """Create a new thing"""
    try:
        thing_controller.store(thing)
        logger.info(f"Created new thing with data: {thing}")
        return {
            "message": "Thing created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating thing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/{id}", response_model=dict)
async def update_thing(id: str, thing: dict):
    """Update an existing thing"""
    try:
        updated_thing = thing_controller.update(id, thing)
        if not updated_thing:
            logger.warning(f"Thing not found with ID: {id}")
            raise HTTPException(status_code=404, detail="Thing not found")
        logger.info(f"Updated thing with ID: {id}")
        return {
            "message": "Thing updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating thing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/{id}", status_code=204)
async def delete_thing(id: str):
    """Delete a thing by ID"""
    try:
        success = thing_controller.destroy(id)
        if not success:
            logger.warning(f"Thing not found with ID: {id}")
            raise HTTPException(status_code=404, detail="Thing not found")
        logger.info(f"Deleted thing with ID: {id}")
        return
    except Exception as e:
        logger.error(f"Error deleting thing: {e}")
        raise HTTPException(status_code=500, detail=str(e))