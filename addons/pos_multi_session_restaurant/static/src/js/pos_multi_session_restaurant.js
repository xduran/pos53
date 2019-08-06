odoo.define('pos_multi_session_restaurant', function(require){
    var screens = require('point_of_sale.screens');
    var models = require('point_of_sale.models');
    var multiprint = require('pos_restaurant.multiprint');
    var floors = require('pos_restaurant.floors');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var chrome = require('point_of_sale.chrome');

    var FloorScreenWidget;
    //console.log('gui', gui.Gui.prototype.screen_classes);
    _.each(gui.Gui.prototype.screen_classes, function(o){
        if (o.name == 'floors'){
            FloorScreenWidget = o.widget;
            FloorScreenWidget.include({
                start: function () {
                    var self = this;
                    this._super();
                    this.pos.bind('change:orders-count-on-floor-screen', function () {
                        self.renderElement();
                    });
                }
            });
            return false;
        }
    });
    var _t = core._t;


    screens.OrderWidget.include({
        update_summary: function(){
            var order = this.pos.get('selectedOrder');
            if (order){
                this._super();
                var buttons = this.getParent().action_buttons;
                if (buttons && buttons.submit_order && this.all_lines_printed(order)) {
                    buttons.submit_order.highlight(false);
                }
            }
        },
        all_lines_printed: function (order) {
            not_printed_line = order.orderlines.find(function(lines){
                                return lines.mp_dirty;
                            });
            return !not_printed_line;
        },
        remove_orderline: function(order_line){
            if (this.pos.get_order() && this.pos.get_order().get_orderlines().length === 0){
                this._super(order_line);
            } else {
                order_line.node.parentNode.removeChild(order_line.node);
            }
        }
    });

    var PosModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
        initialize: function(){
            var self = this;
            PosModelSuper.prototype.initialize.apply(this, arguments);
        },
        ms_create_order: function(options){
            var self = this;
            var order = PosModelSuper.prototype.ms_create_order.apply(this, arguments);
            if (options.data.table_id) {
                order.table = self.tables_by_id[options.data.table_id];
                order.customer_count = options.data.customer_count;
                order.waiter = options.data.waiter;
                order.save_to_db();
            }
            return order;
        },
        ms_do_update: function(order, data){
            PosModelSuper.prototype.ms_do_update.apply(this, arguments);
            if (order) {
                order.set_customer_count(data.customer_count, true);
                order.set_waiter(data.waiter);
                order.saved_resume = data.multiprint_resume;
                this.gui.screen_instances.products.action_buttons.guests.renderElement();
                this.gui.screen_instances.products.action_buttons.waiter.renderElement();
            }
        },
        ms_on_add_order: function(current_order){
            if (!current_order){
                this.trigger('change:orders-count-on-floor-screen');
            }else{
                PosModelSuper.prototype.ms_on_add_order.apply(this, arguments);
            }
        },
        ms_on_update: function(message, sync_all){
            var self = this;
            var data = message.data || {};
            var order = false;
            var old_order = this.get_order();

            if (data.uid){
                order = this.get('orders').find(function(ord) {
                    return ord.uid === data.uid;
                });
            }
            if (order && order.table && order.table.id !== data.table_id) {
                order.transfer = true;
                order.destroy({'reason': 'abandon'});
            }
            PosModelSuper.prototype.ms_on_update.apply(this, arguments);
            if ((order && old_order && old_order.uid !== order.uid) || (old_order === null)) {
                this.set('selectedOrder',old_order);
            }
            if (!sync_all && this.gui.screen_instances.floors && this.gui.get_current_screen() === "floors") {
                this.gui.screen_instances.floors.renderElement();
            }
        },
        set_table: function(table) {
            if (this.change_table){
                if (!table) {
                    this.set_order(null);
                }
                else {
                    this.previous_order_id.table = table;
                    this.change_table = false;
                    this.table = table;
                    this.set_order(this.previous_order_id);
                    this.previous_order_id.ms_update();
                }
            }
            else{
                PosModelSuper.prototype.set_table.apply(this,arguments);
            }
        },
    });

    var OrderSuper = models.Order;
    models.Order = models.Order.extend({
        set_customer_count: function (count, skip_ms_update) {
            OrderSuper.prototype.set_customer_count.apply(this, arguments);
            if (!skip_ms_update) {
                this.ms_update();
            }
        },
        set_waiter: function (waiter, skip_ms_update) {
            OrderSuper.prototype.set_waiter.apply(this, arguments);
            if (!skip_ms_update) {
                this.ms_update();
            }
        },
        printChanges: function(){
            OrderSuper.prototype.printChanges.apply(this, arguments);
            this.just_printed = true;
        },
    });

});
