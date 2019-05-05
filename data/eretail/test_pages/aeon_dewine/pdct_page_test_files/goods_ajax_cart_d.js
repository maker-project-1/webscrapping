jQuery(document).ready(function () {

    if (document.URL.match("cart.aspx")) {
        return false;
    }
    var $btn_cart = jQuery("input.btn_cart_l_,input.btn_cartl_");   
    $btn_cart.unbind("click");
    $btn_cart.bind("click", function (e) {
    
        // 20170203 [ino] ランドセル対応 start
        var base = "";
        var baseObj = document.getElementsByName("bto_base");
        if( baseObj ) {
            base = jQuery(baseObj).attr("value");
        }

        var cover = "";
        var coverObj = document.getElementsByName("bto_cover");
        if( coverObj ) {
            cover = jQuery(coverObj).attr("value");
        }

        var edge = "";
        var edgeObj = document.getElementsByName("bto_edge");
        if( edgeObj ) {
            edge = jQuery(edgeObj).attr("value");
        }
        
        var studs = "";
        var studsObj = document.getElementsByName("bto_studs");
        if( studsObj ) {
            studs = jQuery(studsObj).attr("value");
        }
        
        var interior = "";
        var interiorObj = document.getElementsByName("bto_interior");
        if( interiorObj ) {
            interior = jQuery(interiorObj).attr("value");
        }
        
        var key_color = "";
        var key_colorObj = document.getElementsByName("bto_key_color");
        if( key_colorObj ) {
            key_color = jQuery(key_colorObj).attr("value");
        }
        
        var initial = "";
        var initialObj = document.getElementsByName("bto_initial");
        if( initialObj ) {
            initial = jQuery(initialObj).attr("value");
        }
        
        var ransel_id = "";
        var ranselIdObj = document.getElementsByName("bto_ransel_id");
        if( ranselIdObj ) {
            ransel_id = jQuery(ranselIdObj).attr("value");
        }
        
        var ransel = "";
        var ranselObj = document.getElementsByName("bto_ransel");
        if( ranselObj ) {
            ransel = jQuery(ranselObj).attr("value");
        }
        
        if( ransel != "" && (base == "" || cover == "" || edge == "" || studs == "" || interior == "" ||  key_color == "" || ransel_id == "")) {
            alert("カラー情報が取得できませんでした。シミュレータ画面から再度選択してください。");
            return false;
        }
        // 20170203 [ino] ランドセル対応 end
        var goods = $('input[name=goods]').val(); 
        
        jQuery.ajax({
            async: false,
            type: "POST",
            url: EC_WWW_ROOT + "/shop/js/addcartmulti.aspx",
            data: { "goods": goods },
            cache: false,
            ifModified: false,
            dataType: "json",
            
            success: function (obj) {
                
                if (!obj.agree) {
                    s.addCart(obj.vars);
                    //Cxense script
                    var wkStr = obj.vars.split(":");
                    var wkCategory = new Array();
                    for (i = 1; i < 7; i++){
                        if (wkStr[2].length >= i * 2) {
                            wkCategory[i] = wkStr[2].substring(0, i * 2);
                        } else {
                            wkCategory[i] = "";
                        }
                    }
                    cX.callQueue.push(['invoke', function() {
                        cX.setSiteId(stdvar.SiteId);
                        cX.setEventAttributes({ origin: 'aeo-std-' + stdvar.shop,persistedQueryId:stdvar.persistedQueryId});
                        cX.sendEvent('CART',{"shop":stdvar.shop,"item_code":wkStr[3],"category1":wkCategory[1],"category2":wkCategory[2],"category3":wkCategory[3],"category4":wkCategory[4],"category5":wkCategory[5],"category6":wkCategory[6]});
                    }]);
                }
                
                //document.location.href = EC_WWW_ROOT + "/shop/cart/cart.aspx?goods=" + goods;
                
                return true;
            },
            error: function (xhr, status, thrown) {
                return false;
            }
        });
        return true;
    });
});
