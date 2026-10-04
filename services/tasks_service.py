from requests import Session

from clients.kanboard_api import call_api


class TasksService:
    def __init__(self, session: Session):
        self.session = session

    def create_task(self, project_id: int, task_title: str):
        return call_api(
            self.session, 
            "createTask",
            {
                "project_id": project_id,
                "title": task_title
            }
        )

    def get_task(self, task_id: int):
        return call_api(
            self.session, 
            "getTask",
            {
                "task_id": task_id,
            }
        )

    def rename_task(self, task_id: int, new_title: str):
        return call_api(
            self.session,
            "updateTask",
            {
                "id": task_id,
                "title": new_title
            }
        )