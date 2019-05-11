odoo.define('pos_garnish.garnish', function (require) {
"use strict";

    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var chrome = require('point_of_sale.chrome');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    var Model = require('web.DataModel');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;


    models.load_models({
        model: 'product.garnish',
        fields: ['name', 'price_extra', 'garnish_id'],
        loaded: function(self,garnish_list){
            self.garnish_list = garnish_list;
            self.garnish_by_id = {};
            for (var i = 0; i < garnish_list.length; i++) {
                self.garnish_by_id[garnish_list[i].id] = garnish_list[i];
            }
        },
    });

    models.load_fields("product.product", ['to_garnish','order_separated','allowed_garnish', 'valid_garnish_ids', 'stand_alone']);

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this,attr,options);
            this.garnish = this.garnish || [];
        },
        set_garnish: function(garnish){

            garnish = garnish.sort(function(a,b){ return a - b; });
            if(''+this.garnish !== ''+garnish){
                this.garnish = garnish;
                this._recalculate_price();
                this.set_dirty(true);
                this.trigger('change',this);
            }
        },
        get_garnish: function(){
            return this.garnish;
        },
        get_garnish_text: function(){
            var text = "";
            for(var i=0; i<this.garnish.length; i++){
                if(i>0){
                    text = text + ', ';
                }
                text = text + this.pos.garnish_by_id[this.garnish[i]].name;
            }
            return text;
        },
        get_empty_garnish: function(){
            return this.get_product().allowed_garnish - this.garnish.length
        },
        can_be_merged_with: function(orderline){
            if(this.get_product().to_garnish){
                return false;
            }else{
                return _super_orderline.can_be_merged_with.apply(this,arguments);
            }
        },
        clone: function(){
            var orderline = _super_orderline.clone.call(this);
            orderline.garnish = this.garnish;
            return orderline;
        },
        export_as_JSON: function(){
            var json = _super_orderline.export_as_JSON.call(this);
            json.garnish = this.garnish;
            return json;
        },
        init_from_JSON: function(json){
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.garnish = json.garnish;
        },
        get_line_diff_hash: function(){
            var diff_hash = _super_orderline.get_line_diff_hash.call(this);
            if (this.get_garnish()) {
               diff_hash = diff_hash + '|' + this.get_garnish_text();
            }
            return diff_hash;
        },
        get_garnish_hashes: function () {
            var hashes = [];
            var garnish = this.garnish;
            for (var i=0; i<garnish.length; i++){
                var hash = [this.get_line_diff_hash() + '|' + this.pos.garnish_by_id[garnish[i]].garnish_id[0],
                            this.pos.garnish_by_id[garnish[i]].garnish_id[0]]
                hashes.push(hash);
            }
            return hashes;
        },
        _recalculate_price: function(){
            var price = this.product.price;
            var garnish = this.garnish;
            for (var i=0; i<garnish.length; i++){
                price += this.pos.garnish_by_id[garnish[i]].price_extra;
            }
            this.set_unit_price(price);
        },
    });

    var GarnishListWidget = PosBaseWidget.extend({
        template: 'GarnishListWidget',
        init: function(parent, options) {

            var self = this;
            this._super(parent,options);
            this.model = options.model;
            this.garnishwidgets = [];
            this.weight = options.weight || 0;
            this.next_screen = options.next_screen || false;

            this.click_garnish_handler = function(){
                var garnish = self.pos.garnish_by_id[this.dataset.garnishId];
                options.click_garnish_action(garnish);
            };

            this.orderline = options.orderline || false
            this.garnish_list = [];
            if (this.orderline){
                var valid_garnish_ids = this.orderline.get_product().valid_garnish_ids;
                for (var i=0; i<valid_garnish_ids.length; i++){
                    this.garnish_list.push(this.pos.garnish_by_id[valid_garnish_ids[i]]);
                }
            }

        },
        set_garnish_list: function(garnish_list){
            this.garnish_list = garnish_list;
            this.renderElement();
        },
        get_garnish_image_url: function(garnish){
            return window.location.origin + '/web/image?model=product.garnish&field=image_medium&id='+garnish.id;
        },
        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },

        render_garnish: function(garnish){
            var image_url = this.get_garnish_image_url(garnish);
            var garnish_html = QWeb.render('Garnish',{
                    widget:  this,
                    garnish: garnish,
                    image_url: image_url,
                });
            var garnish_node = document.createElement('div');
            garnish_node.innerHTML = garnish_html;
            garnish_node = garnish_node.childNodes[1];
            return garnish_node;
        },

        renderElement: function() {
            var el_str  = QWeb.render(this.template, {widget: this});
            var el_node = document.createElement('div');
                el_node.innerHTML = el_str;
                el_node = el_node.childNodes[1];

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }
            this.el = el_node;

            var list_container = el_node.querySelector('.available-garnish-list');
            for(var i = 0, len = this.garnish_list.length; i < len; i++){
                var garnish_node = this.render_garnish(this.garnish_list[i]);
                garnish_node.addEventListener('click',this.click_garnish_handler);
                list_container.appendChild(garnish_node);
            }

        },

        destroy: function(){
            var new_el = document.createElement('div');
            new_el.innerHTML = '<div class="placeholder-GarnishListWidget" />';
            new_el = new_el.childNodes[0]
            this.el.parentNode.replaceChild(new_el, this.el);
        },
    });

    var GarnishSelectedWidget = GarnishListWidget.extend({
        template: 'GarnishSelectedWidget',

        init: function(parent, options) {
            var self = this;
            this._super(parent,options);

            this.selected_garnish_list = [];
            if (this.orderline){
                var selected_garnish_ids = this.orderline.get_garnish();
                this.allowed_garnish = this.orderline.get_product().allowed_garnish;
                for (var i=0; i<selected_garnish_ids.length; i++){
                    this.selected_garnish_list.push(this.pos.garnish_by_id[selected_garnish_ids[i]]);
                }
            }

        },

        render_empty_garnish: function(){
            var empty_garnish_html = QWeb.render('EmptyGarnish',{});
            var empty_garnish_node = document.createElement('div');
            empty_garnish_node.innerHTML = empty_garnish_html;
            empty_garnish_node = empty_garnish_node.childNodes[1];
            return empty_garnish_node;
        },

        renderElement: function() {
            var el_str  = QWeb.render(this.template, {widget: this});
            var el_node = document.createElement('div');
                el_node.innerHTML = el_str;
                el_node = el_node.childNodes[1];

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }
            this.el = el_node;

            var list_container = el_node.querySelector('.selected-garnish-list');
            for(var i = 0, len = this.selected_garnish_list.length; i < len; i++){
                var garnish_node = this.render_garnish(this.selected_garnish_list[i]);
                garnish_node.addEventListener('click',this.click_garnish_handler);
                list_container.appendChild(garnish_node);
            }
            var empty_garnish = this.allowed_garnish - this.selected_garnish_list.length;
            for(var i=0; i<empty_garnish; i++){
                var empty_garnish_node = this.render_empty_garnish();
                list_container.appendChild(empty_garnish_node);
            }

        },

        destroy: function(){
            var new_el = document.createElement('div');
            new_el.innerHTML = '<div class="placeholder-GarnishSelectedWidget" />';
            new_el = new_el.childNodes[0]
            this.el.parentNode.replaceChild(new_el, this.el);
        },

        save_changes: function(){
            var garnish_list = [];
            for(var i=0; i<this.selected_garnish_list.length; i++){
                garnish_list.push(this.selected_garnish_list[i].id);
            }
            this.orderline.set_garnish(garnish_list);
        },

        clear_selection: function(){
            this.selected_garnish_list = [];
            this.renderElement();
        },

        add_garnish_to_selection: function(garnish){
            var empty_garnish = this.allowed_garnish - this.selected_garnish_list.length;
            if(empty_garnish>0){
                this.selected_garnish_list.push(garnish);
                this.renderElement();
            }
        },
    });

    var GarnishScreenWidget = screens.ScreenWidget.extend({
        template: 'GarnishScreenWidget',

        next_screen: 'products',
        previous_screen: 'products',

        click_garnish: function(garnish) {
           this.selected_garnish_list_widget.add_garnish_to_selection(garnish);
        },

        click_selected_garnish: function(garnish) {

        },

        show: function(){
            var self = this;
            this._super();
            this.renderElement();
            this.selected_garnish_list_widget = new GarnishSelectedWidget(this,{
                click_garnish_action: function(garnish){ self.click_selected_garnish(garnish); },
                orderline: this.gui.get_current_screen_param('orderline'),
            });
            this.selected_garnish_list_widget.replace(this.$('.placeholder-GarnishSelectedWidget'));
            this.garnish_list_widget = new GarnishListWidget(this,{
                click_garnish_action: function(garnish){ self.click_garnish(garnish); },
                orderline: this.gui.get_current_screen_param('orderline'),
            });
            this.garnish_list_widget.replace(this.$('.placeholder-GarnishListWidget'));


            this.$('.back').click(function(){
                self.gui.back();
            });

            this.$('.next').click(function(){
                self.selected_garnish_list_widget.save_changes();
                self.gui.back();
            });

            this.$('.clear').click(function(){
                self.selected_garnish_list_widget.clear_selection();
            });
        },

        close: function(){
            this._super();
            this.selected_garnish_list_widget.destroy();
            this.garnish_list_widget.destroy();
        },
    });
    gui.define_screen({name:'garnish_selection', widget: GarnishScreenWidget});

    var GarnishButton = screens.ActionButtonWidget.extend({
        template: 'GarnishButton',

        button_click: function() {

            var line = this.pos.get_order().get_selected_orderline();
            if (line && line.get_product().to_garnish) {
                this.gui.show_screen('garnish_selection', {orderline: line});
            }
        },
    });

    screens.define_action_button({
            'name': 'garnish',
            'widget': GarnishButton,
            'condition': function(){
                return this.pos.config.iface_garnish;
            },
        },{
            'after': 'submit_order'
        }
    );

    screens.ProductScreenWidget.include({
        click_product: function(product) {
            this._super(product);
            if (product.to_garnish && this.pos.config.iface_garnish && product.allowed_garnish > 0){
                this.gui.show_screen('garnish_selection', {orderline: this.pos.get_order().get_last_orderline()});
            }
        },
    });

    screens.ProductListWidget.include({
        set_product_list: function(product_list){
            var filtered_products = [];
            for(var i=0; i<product_list.length; i++){
                if(product_list[i].stand_alone){
                    filtered_products.push(product_list[i]);
                }
            }
            this._super(filtered_products);
        },
    });

    return {
        GarnishListWidget: GarnishListWidget,
        GarnishSelectedWidget: GarnishSelectedWidget,
        GarnishScreenWidget: GarnishScreenWidget,
        GarnishButton: GarnishButton,
    }

});
