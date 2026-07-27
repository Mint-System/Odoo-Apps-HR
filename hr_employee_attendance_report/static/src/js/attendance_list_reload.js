/** @odoo-module **/

import {ListController} from "@web/views/list/list_controller";
import {registry} from "@web/core/registry";

class AttendanceListController extends ListController {
    async doAction(actionRequest) {
        const result = await super.doAction(actionRequest);
        // If the action is a server action, refresh the list so booleans reflect
        if (result && result.type === "ir.actions.server") {
            this.reload();
        }
        return result;
    }
}

// Register a custom "list" view variant
registry.category("views").add("attendance_list_reload", {
    ...registry.category("views").get("list"),
    Controller: AttendanceListController,
});
