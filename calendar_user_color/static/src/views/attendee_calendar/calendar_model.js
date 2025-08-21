/** @odoo-module **/

import { CalendarModel } from "@web/views/calendar/calendar_model";

export class AttendeeCalendarModelColor extends CalendarModel {
  async updateFilters(fieldName, filters) {
    // Call the original updateFilters method
    console.log("updateFilters", fieldName, filters);
    await super.updateFilters(fieldName, filters);
    

    // Add the userColor property to the filter object
    const section = this.data.filterSections[fieldName];
    if (section) {
      for (const filter of section.filters) {
        if (filter.type === "user") {
          const userColor = await this.orm.call("res.partner", "read", [filter.value, ["color"]])[0].color;
          filter.userColor = userColor;
        }
      }
    }
  }
}