from pydantic import BaseModel


class SetVaultRequest(BaseModel):
    thread_id: str
    vault_path: str
