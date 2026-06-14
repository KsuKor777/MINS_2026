from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .services import MenuService


class ICommand(ABC):
    @abstractmethod
    def execute(self):
        raise NotImplementedError


@dataclass
class CreateCategoryCommand(ICommand):
    menu_service: MenuService
    name: str

    def execute(self):
        return self.menu_service.create_category(self.name)


@dataclass
class CreateMenuItemCommand(ICommand):
    menu_service: MenuService
    category_id: int
    name: str
    price_text: str

    def execute(self):
        return self.menu_service.create_item(self.category_id, self.name, self.price_text)


@dataclass
class CommandBus:
    history: list[str] = field(default_factory=list)

    def execute(self, command: ICommand):
        result = command.execute()
        self.history.append(command.__class__.__name__)
        return result
