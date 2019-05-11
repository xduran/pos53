odoo.define('pos_restaurnt_ext.change_table', function (require) {
    "use strict";

    var chrome = require('point_of_sale.chrome');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;


    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function(session, attributes) {
            this.change_table = false;
            this.previous_order_id= false;
            return _super_posmodel.initialize.call(this,session,attributes);
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
//                    this.previous_order_id.set_customer_count(this.previous_order_id.customer_count);
                }
            }
            else{
                _super_posmodel.set_table.apply(this,arguments);
            }
        },
    });


    var ChangeTableButton = screens.ActionButtonWidget.extend({
        template: 'ChangeTableButton',

        button_click: function () {
            this.pos.change_table = true;
            this.pos.previous_order_id = this.pos.get_order();
            this.pos.set_table(null);
        },
    });

    screens.define_action_button({
            'name': 'change_table',
            'widget': ChangeTableButton,
            'condition': function () {
                return this.pos.config.iface_change_table;
            },
        }
    );

});