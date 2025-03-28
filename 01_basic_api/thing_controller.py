import json
from typing import List, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, ValidationError

class Thing(BaseModel):
    id: str
    name: str

    @classmethod
    def from_dict(cls, data: Dict) -> 'Thing':
        return cls(**data)

class ThingController:
    """
    A class to manage a list of things stored in a JSON file.
    
    Attributes:
        file_path (str): Path to the JSON file containing the things
        things (List[Thing]): List of Thing objects
    """
    
    def __init__(self):
        """Initialize the controller and load existing things from JSON file."""
        self.file_path = "things.json"
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.things = [Thing.from_dict(t) for t in data]
        except FileNotFoundError:
            self.things = []
            with open(self.file_path, 'w') as f:
                json.dump([], f, indent=2)
        except json.JSONDecodeError:
            self.things = []
            with open(self.file_path, 'w') as f:
                json.dump([], f, indent=2)

    def save_to_file(self) -> None:
        """Save the current state of things to the JSON file."""
        with open(self.file_path, 'w') as f:
            json.dump([t.dict() for t in self.things], f, indent=2)

    def store(self, data: Dict) -> None:
        """Create a new thing and add it to the database.
        
        Args:
            data (Dict): Dictionary containing Thing data
        """
        try:
            data['id'] = str(uuid4())
            new_thing = Thing.from_dict(data)
            self.things.append(new_thing)
            self.save_to_file()
        except ValidationError as e:
            raise

    def index(self) -> List[Thing]:
        """Get all things from the database.
        
        Returns:
            List[Thing]: List of all things
        """
        return self.things

    def show(self, id: str) -> Optional[Thing]:
        """Get a single thing by ID.
        
        Args:
            id (str): ID of the thing to retrieve
            
        Returns:
            Optional[Thing]: The thing if found, None otherwise
        """
        return next((thing for thing in self.things if thing.id == id), None)

    def update(self, id: str, data: Dict) -> Optional[Thing]:
        """Update an existing thing.
        
        Args:
            id (str): ID of the thing to update
            data (Dict): Dictionary containing fields to update
            
        Returns:
            Optional[Thing]: The updated thing if found, None otherwise
        """
        thing = self.show(id)
        if not thing:
            return None
            
        try:
            updated_thing = thing.copy(update=data)
            self.things = [t if t.id != id else updated_thing for t in self.things]
            self.save_to_file()
            return updated_thing
        except ValidationError as e:
            raise

    def destroy(self, id: str) -> bool:
        """Delete a thing by ID.
        
        Args:
            id (str): ID of the thing to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        initial_length = len(self.things)
        self.things = [thing for thing in self.things if thing.id != id]
        
        if len(self.things) == initial_length:
            return False
            
        self.save_to_file()
        return True