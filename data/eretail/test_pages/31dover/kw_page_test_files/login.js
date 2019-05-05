// AMZN PAY SDK 9/28/2018, 10:38:11 PM
if (window.amazon == null || window.amazon.Login == null) {
(function() {
'use strict';var g,k,q,v,w,x;function aa(b,a){null!==b&&b||(b={});for(var d=1;d<arguments.length;d++){var c=arguments[d];if(null!==c&&void 0!==c)for(var e in c)b[e]=c[e]}return b}function y(b,a){var d=z.apply(void 0,arguments);A("error",d);throw Error(d);}function ba(b,a){var d=z.apply(void 0,arguments);A("warn",d)}
function z(b,a){var d=arguments,c=1;return b.replace(/%((%)|[sid])/g,function(a){if(a[2])return a[2];a=d[c++];"object"==typeof a&&window.JSON&&window.JSON.stringify&&(a=window.JSON.stringify(a));return a})}function A(b,a){window.console&&window.console.log&&("function"==typeof a&&(a=a()),a=z("[Amazon.%s] %s",b,a),window.console.log(a))}function ea(b){b&&"delegate"===b||y("expected %s value to be %s but was %s","options.response_type","delegate",b)}
function B(b,a,d){null==a&&y("missing %s",b);typeof a!=d&&y("expected %s to be a %s",b,d)}
function D(b){var a=document.getElementById(b);a||(a=document.createElement("div"),a.setAttribute("id",b),a.setAttribute("width",0),a.setAttribute("height",0),a.setAttribute("style","position: absolute; left: -1000px; top: -1000px"),a.style.setAttribute&&a.style.setAttribute("cssText","position: absolute; left: -1000px; top: -1000px"),b=document.getElementById("amazon-root"),b||(b=document.createElement("div"),b.setAttribute("id","amazon-root"),document.body.appendChild(b)),b.appendChild(a));return a}
function fa(){var b=D("amazon-client-credentials-root"),a=la(16),d=document.createElement("iframe");d.setAttribute("name",a);b.appendChild(d);document.getElementsByName(a).length||(b.removeChild(d),d=document.createElement('\x3ciframe name\x3d"'+a+'"/\x3e'),b.appendChild(d));d.setAttribute("id",a);return a}function ma(){this.a=[]}function qa(b,a,d){b.a.push({X:a,ca:!!d})}
ma.prototype.b=function(b){var a=this.a;this.a=[];for(var d=0;d<a.length;d++)a[d].ca&&this.a.push(a[d]);for(d=0;d<a.length;d++)a[d].X.apply(void 0,arguments)};
var E=function(){function b(){switch(f){case "t":return e("t"),e("r"),e("u"),e("e"),!0;case "f":return e("f"),e("a"),e("l"),e("s"),e("e"),!1;case "n":return e("n"),e("u"),e("l"),e("l"),null}h("Unexpected '"+f+"'")}function a(){for(;f&&" ">=f;)e()}function d(){var a,b,d="",c;if('"'===f)for(;e();){if('"'===f)return e(),d;if("\\"===f)if(e(),"u"===f){for(b=c=0;4>b;b+=1){a=parseInt(e(),16);if(!isFinite(a))break;c=16*c+a}d+=String.fromCharCode(c)}else if("string"===typeof n[f])d+=n[f];else break;else d+=
f}h("Bad string")}function c(){var a;a="";"-"===f&&(a="-",e("-"));for(;"0"<=f&&"9">=f;)a+=f,e();if("."===f)for(a+=".";e()&&"0"<=f&&"9">=f;)a+=f;if("e"===f||"E"===f){a+=f;e();if("-"===f||"+"===f)a+=f,e();for(;"0"<=f&&"9">=f;)a+=f,e()}a=+a;if(isFinite(a))return a;h("Bad number")}function e(a){a&&a!==f&&h("Expected '"+a+"' instead of '"+f+"'");f=r.charAt(l);l+=1;return f}function h(a){throw{name:"SyntaxError",message:a,ka:l,text:r};}var l,f,n={'"':'"',"\\":"\\","/":"/",la:"\b",ma:"\f",n:"\n",r:"\r",
t:"\t"},r,C;C=function(){a();switch(f){case "{":var n;a:{var l={};if("{"===f){e("{");a();if("}"===f){e("}");n=l;break a}for(;f;){n=d();a();e(":");Object.hasOwnProperty.call(l,n)&&h('Duplicate key "'+n+'"');l[n]=C();a();if("}"===f){e("}");n=l;break a}e(",");a()}}h("Bad object");n=void 0}return n;case "[":a:{n=[];if("["===f){e("[");a();if("]"===f){e("]");break a}for(;f;){n.push(C());a();if("]"===f){e("]");break a}e(",");a()}}h("Bad array");n=void 0}return n;case '"':return d();case "-":return c();default:return"0"<=
f&&"9">=f?c():b()}};return function(b,d){r=b;l=0;f=" ";b=C();a();f&&h("Syntax error");return"function"===typeof d?function m(a,b){var c,e,f=a[b];if(f&&"object"===typeof f)for(c in f)Object.prototype.hasOwnProperty.call(f,c)&&(e=m(f,c),void 0!==e?f[c]=e:delete f[c]);return d.call(a,b,f)}({"":b},""):b}}(),I=function(){function b(a){return 10>a?"0"+a:a}function a(a){c.lastIndex=0;return c.test(a)?'"'+a.replace(c,function(a){var b=l[a];return"string"===typeof b?b:"\\u"+("0000"+a.charCodeAt(0).toString(16)).slice(-4)})+
'"':'"'+a+'"'}function d(b,c){var l,n,r=e,t,m=c[b];m&&"object"===typeof m&&"function"===typeof m.toJSON&&(m=m.toJSON(b));"function"===typeof f&&(m=f.call(c,b,m));switch(typeof m){case "string":return a(m);case "number":return isFinite(m)?String(m):"null";case "boolean":case "null":return String(m);case "object":if(!m)return"null";e+=h;t=[];if("[object Array]"===Object.prototype.toString.apply(m)){n=m.length;for(b=0;b<n;b+=1)t[b]=d(b,m)||"null";c=t.length?e?"[\n"+e+t.join(",\n"+e)+"\n"+r+"]":"["+t.join(",")+
"]":"[]";e=r;return c}if(f&&"object"===typeof f)for(n=f.length,b=0;b<n;b+=1)"string"===typeof f[b]&&(l=f[b],(c=d(l,m))&&t.push(a(l)+(e?": ":":")+c));else for(l in m)Object.prototype.hasOwnProperty.call(m,l)&&(c=d(l,m))&&t.push(a(l)+(e?": ":":")+c);c=t.length?e?"{\n"+e+t.join(",\n"+e)+"\n"+r+"}":"{"+t.join(",")+"}":"{}";e=r;return c}}"function"!==typeof Date.prototype.toJSON&&(Date.prototype.toJSON=function(){return isFinite(this.valueOf())?this.getUTCFullYear()+"-"+b(this.getUTCMonth()+1)+"-"+b(this.getUTCDate())+
"T"+b(this.getUTCHours())+":"+b(this.getUTCMinutes())+":"+b(this.getUTCSeconds())+"Z":null},String.prototype.toJSON=Number.prototype.toJSON=Boolean.prototype.toJSON=function(){return this.valueOf()});var c=/[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,e,h,l={"\b":"\\b","\t":"\\t","\n":"\\n","\f":"\\f","\r":"\\r",'"':'\\"',"\\":"\\\\"},f;return function(a,b,c){var l;h=e="";if("number"===typeof c)for(l=0;l<c;l+=1)h+=" ";else"string"===
typeof c&&(h=c);if((f=b)&&"function"!==typeof b&&("object"!==typeof b||"number"!==typeof b.length))throw Error("JSON.stringify");return d("",{"":a})}}();function J(b){var a="",d;for(d in b)a&&(a+="\x26"),a+=encodeURIComponent(d)+"\x3d"+encodeURIComponent(b[d]+"");return a}
(function(){function b(a,b){for(var d=0;d<b.length;d++){var e=b[d];""==e||a.b.hasOwnProperty(e)||(a.a.push(e),a.b[e]=1)}}k=function(a){this.a=[];a="string"==typeof a?a.split(/\s+/):a;this.b={};b(this,a)};k.prototype.contains=function(a){for(var b=0;b<a.a.length;b++)if(!this.b.hasOwnProperty(a.a[b]))return!1;return!0};k.prototype.add=function(a){b(this,a.a)};k.prototype.c=function(a){for(var b=0;b<this.a.length;b++)a(this.a[b])};k.prototype.toString=function(){return this.a.join(" ")}})();
(function(){q={};var b=null;q.m=function(){return b};q.o=function(a){B("domain",a,"string");a=a.replace(/^\s+|\s+$/g,"");var d="."+window.location.hostname;"."!=a.charAt(0)&&(a="."+a);d.indexOf(a)!=d.length-a.length&&y("Site domain must contain the current page's domain");b=a};q.v=function(){};q.v.prototype.getItem=function(){};q.v.setItem=function(){};q.v.removeItem=function(){}})();
(function(){function b(){}b.prototype.getItem=function(a){return(a=(new RegExp("(?:^|;)\\s*"+escape(a).replace(/[\-\.\+\*]/g,"\\$\x26")+"\\s*\\\x3d\\s*([^;]*)(?:;|$)")).exec(document.cookie))?unescape(a[1]):null};b.prototype.setItem=function(a,b,c){var d;d=null==c?"Fri, 31 Dec 9999 23:59:59 GMT":(new Date((new Date).getTime()+1E3*c)).toGMTString();var h=q.m(),h=null==h?"":";Domain\x3d"+h,l=ra(K())?"":";Secure";document.cookie=a+"\x3d"+escape(b)+("session"==c?"":";Expires\x3d"+d)+h+";Path\x3d/"+l};
b.prototype.removeItem=function(a){q.f.setItem(a,"null",0)};q.f=new b})();(function(){function b(a){this.a=a}b.prototype.getItem=function(a){return this.a.getItem(a)};b.prototype.setItem=function(a,b,c){this.a.setItem(a,b,c)};b.prototype.removeItem=function(a){q.f.removeItem(a)};q.l=new b(q.f)})();
(function(){function b(a){var b;try{b=E(a).clear}catch(c){b=void 0}b&&(console.log("Deleting cache cookie now."),q.l.removeItem("amazon_Login_state_cache"))}v={V:function(a,b){"bearer"==a.token_type&&(a={access_token:a.access_token,max_age:b,expiration_date:(new Date).getTime()+1E3*b,client_id:w.I(),scope:a.scope},M()&&(a.domain=w.m()),a=I(a),q.l.setItem("amazon_Login_state_cache",a,"session"))},H:function(){var a=q.l.getItem("amazon_Login_state_cache");if(null!=a&&(a=E(a),null!=a&&a.expiration_date>
(new Date).getTime())){if(M()&&"undefined"!=typeof a.domain&&a.domain!=w.m())return null;a.scope=new k(a.scope);return a}return null},W:function(){var a=N(w.K(),"/checkout/clear",null,null).toString(),d="?coe\x3d"+w.G()+"\x26env\x3d"+w.J(),c;if(window.XDomainRequest)c=new window.XDomainRequest,c.onload=function(){b(c.responseText)};else{var e=!1;c=new window.XMLHttpRequest;c.onreadystatechange=function(){e||4!=c.readyState||(e=!0,b(c.responseText))}}c.open("GET",a+d,!0);c.withCredentials=!0;c.send(null)},
w:function(){q.l.removeItem("amazon_Login_state_cache")}}})();function sa(){return window.XMLHttpRequest&&"withCredentials"in new window.XMLHttpRequest||"undefined"!==typeof window.XDomainRequest?!0:!1}function O(b,a,d,c,e,h){this.a=new P(b,a,d);"string"==typeof c&&c||y("missing or invalid path: %s",c);this.i=c;"object"==typeof e&&(e=J(e));e&&"string"!=typeof e&&y("invalid query: %s",e);this.c=e||"";"object"==typeof h&&(h=J(h));h&&"string"!=typeof h&&y("invalid fragment: %s",h);this.b=h||""}
function Q(b){var a=function(){var a=document.createElement("div");a.innerHTML="\x3ca\x3e\x3c/a\x3e";a.firstChild.href=b;a.innerHTML=a.innerHTML;return a.firstChild}();""==a.host&&(a.href=a.href);return new O(a.protocol,a.hostname,function(){var b=a.port;b&&"0"!=b||(b=null);return b}(),function(){var b=a.pathname;b?"/"!=b[0]&&(b="/"+b):b="/";return b}(),a.search.substring(1),a.href.split("#")[1]||"")}function K(){return Q(window.location.href+"")}g=O.prototype;g.scheme=function(){return this.a.scheme()};
g.host=function(){return this.a.host()};g.port=function(){return this.a.port()};g.path=function(){return this.i};g.query=function(){return this.c};g.h=function(){return this.b};function ra(b){var a="http"==b.a.scheme();b=b.a.host();return a&&("localhost"==b||"127.0.0.1"==b)}g.toString=function(){var b=this.a.toString(),b=b+this.i,b=b+(this.c?"?"+this.c:"");return b+=this.b?"#"+this.b:""};
function ta(b,a){return new O(void 0!==a.scheme?a.scheme:b.scheme(),void 0!==a.host?a.host:b.host(),void 0!==a.port?a.port:b.port(),void 0!==a.path?a.path:b.path(),void 0!==a.query?a.query:b.query(),void 0!==a.h?a.h:b.h())}
function P(b,a,d){var c;"string"==typeof b&&(c=b.match(/^(https?)(:(\/\/)?)?$/i))||y("missing or invalid scheme: %s",b);this.a="http"==c[1]?"http":"https";if(b="string"==typeof a&&a)"string"==typeof a&&a||y("missing or invalid input: %s",a),b=a.replace(/^\s+|\s+$/g,"").length;b||y("missing or invalid host: %s",a);this.c=a;d&&((d+"").match(/^\d+$/)||y("invalid port: %s",d),80==d&&"http"==this.a||443==d&&"https"==this.a)&&(d=null);this.b=d?d+"":null}var ua=/^(http|https):\/\/(.+?)(:(\d+))?$/i;
P.prototype.scheme=function(){return this.a};P.prototype.host=function(){return this.c};P.prototype.port=function(){return this.b};P.prototype.toString=function(){var b;b=""+(this.a+"://");b+=this.c;return b+=this.b?":"+this.b:""};function N(b,a,d,c){return new O(b.a,b.c,b.b,a,d,c)}function la(b){for(var a="",d=0;d<b;d++)a+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(62*Math.random()));return a}var R={},X=null;
function va(b,a,d){if(window.__toucanForceProxyOriginTo){b=window.__toucanForceProxyOriginTo;var c=b.match(ua);if(c)b=new P(c[1],c[2],c[4]?c[4]-0:null);else throw y("invalid origin: %s",b),Error();}else if(window.__toucanForceProxyOriginToThisOrigin)b=K().a;else if(c=b.host().match(/^([\w\-\.]+\.)?amazon\.([\w\.]+)$/))c="api-cdn.amazon."+c[2],a&&(c=b.host()),"https"==b.scheme()?b=new P("https",c,null):(y("no proxy origin; unsupported non-https target origin for amazon: %s",b),b=void 0);else throw y("no proxy origin; unsupported target origin: %s",
b),Error();var c=ya(b),e=b,h;a?h="amazon-proxy-iframe-name":(h=e.host().replace(/[^a-z0-9]/ig,"_"),e.port()&&(h+="_"+e.port()),h=z("amazon-proxy-%s-%s",e.scheme(),h));var l=document.getElementById(h);l||(l=document.createElement("iframe"),l.setAttribute("id",h),l.setAttribute("name",h),l.setAttribute("src",Ca(e,c,a).toString()),D("amazon-proxy-root").appendChild(l));a=h;c=la(16);R[c]||(R[c]=new ma);qa(R[c],d,!1);d=b;a={uri:Da().toString(),proxy:a,topic:c,version:"1"};return N(d,"/sdk/2018-02-08-63k6q26l/topic.html",
a,"")}function ya(b){X||(X=Ea(),X.M(b,function(a,b){(a=R[a])&&a.b(b)}));return X}function Da(){return ta(Q(window.location.href+""),{query:"",h:""})}function Ca(b,a,d){a={uri:Da().toString(),tr:a.name()};return N(b,(d?"/static/sdk":"/sdk/2018-02-08-63k6q26l")+"/proxy.html",d?"":{version:"1"},a)}var Fa=/^ABMNZNXDC;([\w\d\_\-]+);(.*)$/;
function Ga(b){var a=b.match(Fa);if(a){b={};b.id=a[1];for(var d={},a=a[2].split("\x26"),c=0;c<a.length;c++){var e=a[c].split("\x3d");2==e.length&&(d[e[0]]=decodeURIComponent(e[1].replace(/\+/g," ")))}b.data=d;return b}return null}function Ea(){var b=window.postMessage?"pm":"fr";window.__toucanForceTransport&&(b=window.__toucanForceTransport);if("pm"==b)b=new Y;else if("fr"==b)b=new Z;else throw y("unknown transport: %s",b),Error();return b}function Y(){this.a=void 0}Y.prototype.name=function(){return"pm"};
function Ia(b){if(void 0===b.a){var a=b.a=new ma;b=function(b){var c;(c=Ga(b.data))&&a.b(b.origin,c.id,c.data)};window.addEventListener?window.addEventListener("message",b,!1):window.attachEvent?window.attachEvent("onmessage",b):y("cannot attach message event")}}
Y.prototype.M=function(b,a){Ia(this);var d=b.toString();qa(this.a,function(b,e,h){var c=K().a.toString();b!=d&&b!=c?ba("Either message from %s does not match proxy origin %s or message from %s does not match current window origin %s",b,d,b,c):a(e,h)},!0)};Y.prototype.send=function(b,a,d){var c=b.a,e=E(I(d));setTimeout(function(){window.parent.postMessage(z("%s;%s;%s","ABMNZNXDC",a,J(e)),c.toString())},1)};function Z(){}Z.prototype.name=function(){return"fr"};
Z.prototype.M=function(b,a){window.__toucanInvokeFragment=function(b,c){a(b,c)}};Z.prototype.send=function(b,a,d){var c=b.query();(c=c||"")&&(c+="\x26");c=c+"ABMNZNXDC"+("\x3d"+la(8));b=ta(b,{query:c,h:z("%s;%s;%s","ABMNZNXDC",a,J(d))});a=document.createElement("iframe");a.setAttribute("src",b.toString());document.body.appendChild(a)};var Ja=window.location.href.split("#")[1]||"";
if(Ja){var Ka=Ga(Ja);Ka&&(document.documentElement.style.display="none","function"==typeof window.parent.parent.__toucanInvokeFragment&&window.parent.parent.__toucanInvokeFragment(Ka.id,Ka.data))}
(function(){function b(a){var b=a.match(Ha);b||y("invalid domain: %s",a);var p=b[2]?b[2].toLowerCase():"https";"https"!=p&&y("invalid domain: %s; scheme must be https",a);a=b[3];a.match(/^amazon\.[a-z\.]+$/)&&(a="www."+a);return new P(p,a,b[5])}function a(a){a=aa({interactive:void 0,popup:!0,response_type:"token",response_mode:void 0,delegated_requests:void 0,direct_post_uri:void 0,state:void 0,scope:void 0,scope_data:void 0,optional_scope:void 0,"com.amazon.oauth2.options":void 0,workflow_data:void 0},
a||{});B("options.response_type",a.response_type,"string");a.response_mode&&B("options.response_mode",a.response_mode,"string");a.direct_post_uri&&B("options.direct_post_uri",a.direct_post_uri,"string");var b=a.delegated_requests;if(b){ea(a.response_type);a.scope&&y("options.scope is not supported for delegated authorization");a.scope_data&&y("options.scope_data is not supported for delegated authorization");a.optional_scope&&y("options.optional_scope is not supported for delegated authorization");
a.interactive?a.interactive!=u.ALWAYS&&y("options.interactive should be '"+u.ALWAYS+"' for delegated authorization"):a.interactive=u.ALWAYS;for(var p={},f=0;f<b.length;f++){var l=b[f],n=d(a,l);p[l.request_id]=n}a.delegated_requests=p}else if(c(a,"missing options.scope"),e(a),h(a),a.interactive?a.interactive!=u.s&&a.interactive!=u.ALWAYS&&a.interactive!=u.NEVER&&y("expected options.interactive to be one of '"+u.s+"', '"+u.ALWAYS+"', or '"+u.NEVER+"'"):a.interactive=u.s,a.optional_scope){a.optional_scope.constructor!==
Array&&"string"!=typeof a.optional_scope&&y("expected options.optional_scope to be a string or array");a.interactive!=u.NEVER&&y("options.optional_scope is only supported for options.interactive \x3d never");b=new k(a.optional_scope);a.scope.add(b);var m={id_token:{}};b.c(function(a){m.id_token[a]={essential:!1}});a.optional_scope=I(m)}return a}function d(a,b){b.response_mode&&y("response_mode is not supported in delegated requests");b.direct_post_uri&&y("direct_post_uri is not supported in delegated requests");
"popup"in b&&y("popup is not supported in delegated requests");b.interactive&&y("interactive mode is not supported in delegated requests");b.optional_scope&&y("optional_scope is not supported in delegated requests");b.delegated_requests&&y("delegated_requests is not supported in delegated requests");null==b.response_type&&(b.response_type="token");c(b,"missing 'scope' in delegated request");b.scope=b.scope.toString();e(b);h(a);B("request_id",b.request_id,"string");b.client_id&&!b.client_id.match(pa)&&
y("invalid client_id format: %s",b.client_id);a={};for(var p in b)"request_id"!=p&&(a[p]=b[p]);return a}function c(a,b){a.scope||y(b);a.scope.constructor!==Array&&"string"!=typeof a.scope&&y("expected scope to be a string or array");a.scope=new k(a.scope)}function e(a){a.scope_data&&(a.scope_data=I(a.scope_data))}function h(a){if(a.workflow_data){var b={};b.workflow_data=a.workflow_data;a["com.amazon.oauth2.options"]=I(b)}}function l(a){var b=(void 0!==window.screenX?window.screenX:window.screenLeft)+
Math.floor(((void 0!==window.outerWidth?window.outerWidth:document.documentElement.clientWidth)-800)/2),c=(void 0!==window.screenY?window.screenY:window.screenTop)+Math.floor(((void 0!==window.outerHeight?window.outerHeight:document.documentElement.clientHeight)-540)/2),b=z("left\x3d%s,top\x3d%s,width\x3d%s,height\x3d%s,scrollbars\x3d1",0>b?0:b,0>c?0:c,800,540);L=window.open(a.toString(),"amazonloginpopup",b)}function f(){L&&("function"==typeof L.close&&L.close(),L=null)}function n(a,b,c,d,f){b={client_id:S,
redirect_uri:b,response_type:a.response_type,language:wa,ui_locales:xa};a["com.amazon.oauth2.options"]&&(b["com.amazon.oauth2.options"]=a["com.amazon.oauth2.options"]);a.response_mode&&(b.response_mode=a.response_mode);a.scope&&(b.scope=a.scope.toString());a.direct_post_uri&&(b.direct_post_uri=a.direct_post_uri);a.scope_data&&(b.scope_data=a.scope_data);ga&&(b.sandbox=!0);a.state&&(b.state=a.state);c&&(b.exac=c,f&&(b.exacde=d));a.delegated_requests&&(b.delegated_requests=I(a.delegated_requests));
f&&(b.coe=T,b.ledger_currency=ha,b.env=U);F=La(oa,!f);return f?N(G,F,b):N(H,F,b)}function r(a,b,c){V=!1;null!=b.access_token?(c=parseInt(b.expires_in,10),c=60>=c?c:c-Math.min(Math.floor(.1*c),300),v.V(b,c),w.R()?q.f.setItem(w.g,b.access_token,c):q.f.removeItem(w.g)):c&&q.f.removeItem(w.g);a.L(b);a=ia;ia=[];for(b=0;b<a.length;b++)na(a[b])}function C(a,b,c,d){var e=J(a);!c&&d?(a=Q(b),a=ta(a,{h:e})):(b+=-1==b.indexOf("?")?"?":"\x26",b+=e,a=Q(b));e=K();"https"==a.scheme()||ra(a)||y("attempted redirect to %s but scheme is not HTTPS",
b);a.host()!=e.host()&&y("attempted redirect to %s but it does not match current host %s",a.host(),e.host());!c&&d?window.top.location.href=a.toString():(f(),window.location.href=b)}function ca(a){var b=this;this.a=a;this.c=null;this.A=[];this.i=null;this.b={status:null,onComplete:function(a){"string"!=typeof a&&"function"!=typeof a&&y("onComplete expects handler parameter to be a function or a string");var c=b.b.status==W.D;"string"==typeof a?c?C(b.i,a,b.a.popup,"token"==b.a.response_type):b.c=a:
"function"==typeof a&&(c?setTimeout(function(){a(b.b)},0):b.A.push(a));return b.b}}}function na(a){var b=a.a,c=null,c=!b.popup,d=Ma(b.scope,c,c?a.c:null,c?window.location.hostname:null);if(b.delegated_requests)t(a,null,0,!1);else{if(b.interactive==u.ALWAYS)v.w();else{var f=null,e=null;w.R()&&(f=q.f.getItem(w.g));if(c=v.H())"token"==b.response_type&&b.scope.add(c.scope),f?f!=c.access_token&&(v.w(),c=null):(f=c.access_token,e=c.expiration_date);var p;if(c&&c.scope.contains(b.scope)&&"token"==b.response_type)p=
{access_token:c.access_token,token_type:"bearer",expires_in:Math.floor((c.expiration_date-(new Date).getTime())/1E3),scope:c.scope.toString()},null!=b.state&&(p.state=b.state);else if(b.interactive==u.NEVER&&b.popup){if(V){ia.push(a);a.B(W.T);return}if(f){m(a,f,e,d);return}p={error:"invalid_grant",error_description:"invalid grant"}}if(p){setTimeout(function(){a.L(p)},0);return}}t(a,f,e,d)}}function t(a,b,c,d){var e=a.a;if(e.popup)V=!0,e=va(d?G:H,d,function(b){f();r(a,b,!0)}),b=n(a.a,e,b,c,d),l(b);
else{var p=a.c;p||y("Missing redirectUrl for redirect flow");window.top.location.href=n(e,Q(p+""),b,c,d).toString()}}function m(a,b,c,d){V=!0;var f=D("amazon-client-credentials-root"),e=fa(),p=document.createElement("form");f.appendChild(p);p.setAttribute("method","POST");p.setAttribute("target",e);var h=a.a,l=va(d?G:H,d,function(b){f.removeChild(p);var c=document.getElementById(e);c&&c.parentNode&&c.parentNode.removeChild(c);b||(b={error:"server_error",description:"Server error."});r(a,b,!1)});b=
{client_id:S,exac:b,grant_type:"client_credentials",redirect_uri:l,response_type:h.response_type,scope:h.scope};null!=h.state&&(b.state=h.state);null!=h.response_mode&&(b.response_mode=h.response_mode);null!=h.direct_post_uri&&(b.direct_post_uri=h.direct_post_uri);null!=h.scope_data&&(b.scope_data=h.scope_data);null!=h.optional_scope&&(b.claims=h.optional_scope);null!=h["com.amazon.oauth2.options"]&&(b["com.amazon.oauth2.options"]=h["com.amazon.oauth2.options"]);d&&(b.exacde=c,b.coe=T,b.ledger_currency=
ha,b.env=U);F=La(oa,!d);c=d?N(G,F,b).toString():N(H,F,b).toString();p.setAttribute("action",c);p.submit()}w={U:{NorthAmerica:"NA",Europe:"EU",AsiaPacific:"APAC",UnitedStates:"US",UnitedKindom:"UK",Germany:"DE",Italy:"IT",France:"FR",Spain:"ES",Japan:"JP"},u:[],g:"amazon_Login_accessToken"};var da={NA:["https://www.amazon.com","https://api.amazon.com"],EU:["https://eu.account.amazon.com","https://api.amazon.co.uk"],APAC:["https://apac.account.amazon.com","https://api.amazon.co.jp"],US:["https://payments.amazon.com",
"https://api.amazon.com"],UK:["https://pay.amazon.co.uk","https://api.amazon.co.uk"],DE:["https://pay.amazon.de","https://api.amazon.co.uk"],IT:["https://pay.amazon.it","https://api.amazon.co.uk"],FR:["https://pay.amazon.fr","https://api.amazon.co.uk"],ES:["https://pay.amazon.es","https://api.amazon.co.uk"],JP:["https://pay.amazon.co.jp","https://api.amazon.co.jp"]},oa={lwa_general:"/ap/oa",connectedAuth_general:"/checkout/authCreate"},pa=/^[\w\-\.]+$/,Ha=/^((http|https):\/\/)?([a-z0-9\-\.]+)(:(\d+))?\/?$/i,
u={ALWAYS:"always",s:"auto",NEVER:"never"},L=null,V=!1,ia=[],W={T:"queued",S:"in_progress",D:"complete"},S=void 0,T=void 0,ha=void 0,za=void 0,U=void 0,F="/ap/oa";w.j=function(a){0>w.u.indexOf(a)&&w.u.push(a)};w.I=function(){w.j("getClientId-api-metric");return S};w.da=function(a){a.match(pa)||y("invalid client ID: %s",a);S=a};w.P=function(a,b,c){T=a;ha=b;U=c};w.ga=function(a){za=a};w.$=function(){return za};var ja="www.amazon.com",ka="www.amazon.com",G=new P("https",ja,null),H=new P("https",ka,null),
Aa=new P("https","api.amazon.com",null);w.m=function(){return ja};w.na=function(){return ka};w.Y=function(){return Aa};w.G=function(){return T};w.J=function(){return U};var ga=!1;w.ia=function(a){"number"==typeof a&&(a=!!a);B("sandboxMode",a,"boolean");ga=a};w.aa=function(){return ga};w.o=function(a){G=b(a);ja=a};w.O=function(a){H=b(a);ka=a};w.C=function(a){w.j("setAPIDomain-api-metric");Aa=b(a)};w.ha=function(a){w.j("setRegion-api-metric");a&&a in da?2==da[a].length?w.C(da[a][1]):y("missing domain or api domain configuration for given region."):
(w.o("https://www.amazon.com"),w.O("https://www.amazon.com"),w.C("https://api.amazon.com"))};var wa="";w.ea=function(a){w.j("setLanguage-api-metric");wa=a};var xa="";w.fa=function(a){w.j("setLanguageHint-api-metric");xa=a};w.K=function(){return G};w.Z=function(){return H};var Ba=!1;w.R=function(){return Ba};w.ja=function(a){null==a?y("missing useCookie"):"number"==typeof a?a=!!a:"boolean"!=typeof a&&y("expected useCookie to be a boolean");Ba=a};ca.prototype.L=function(a){this.i=a;aa(this.b,a);this.B(W.D);
for(a=0;a<this.A.length;a++)this.A[a](this.b);null!=this.c&&C(this.i,this.c,this.a.popup,"token"==this.a.response_type)};ca.prototype.B=function(a){this.b.status=a};w.F=function(b,c){2>arguments.length&&y("authorize expects two arguments (options, next)");b&&"object"!=typeof b&&y("authorize expects options parameter to be an object");null!=c&&"function"!=typeof c&&"string"!=typeof c&&y("authorize expects next parameter to be a function or a string");b=a(b);var d=new ca(b),f=d.b;d.B(W.S);if(null!=
c)f.onComplete(c);b.popup||"string"==typeof c?na(d):y("next must be redirect URI if !options.popup");return f}})();
(function(){function b(a,b){var c;try{c=E(a)}catch(e){c=null}c&&c.Error?(a={success:!1},a.error=z("%s: %s",c.Error.Code||"UnknownError",c.Error.Message||"An unknown error occurred"),b(a)):c&&c.Profile?(a={success:!0},a.profile=c.Profile,b(a)):(a={success:!1,error:"UnknownError: Incomprehensible response from profile endpoint"},b(a))}x={N:function(a,d){if(null==d&&"function"==typeof a)d=a,w.F({scope:"profile"},function(a){null==a.error?x.N(a.access_token,d):d({success:!1,error:a.error})});else if(B("accessToken",
a,"string"),B("callback",d,"function"),sa()){a=N(w.Z(),"/ap/user/profile",{access_token:a},"").toString();var c;if(window.XDomainRequest)c=new window.XDomainRequest,c.onload=function(){b(c.responseText,d)};else{var e=!1;c=new window.XMLHttpRequest;c.onreadystatechange=function(){e||4!=c.readyState||(e=!0,b(c.responseText,d))}}c.open("GET",a,!0);c.send()}else d({success:!1,error:"UnsupportedOperation: Cannot retrieve profile in this browser"})}}})();
(function(){function b(){var a=N(w.K(),"/checkout/logout",null,null).toString(),b="?coe\x3d"+w.G()+"\x26env\x3d"+w.J()+"\x26mID\x3d"+w.$(),c;if(window.XDomainRequest)c=new window.XDomainRequest,c.onload=function(){d(c.responseText)};else{var e=!1;c=new window.XMLHttpRequest;c.onreadystatechange=function(){e||4!=c.readyState||(e=!0,d(c.responseText))}}c.open("GET",a+b,!0);c.withCredentials=!0;c.send(null)}function a(a){sa()||e("UnsupportedOperation: Cannot remotely logout in this browser");var b=N(w.Y(),
"/auth/relyingPartyLogout",null,null).toString(),d={};d.token=a;d.token_type="bearer";var h;if(window.XDomainRequest)h=new window.XDomainRequest,h.onload=function(){c(h.responseText)};else{var r=!1;h=new window.XMLHttpRequest;h.onreadystatechange=function(){r||4!=h.readyState||(r=!0,c(h.responseText))}}h.open("POST",b,!0);h.send(I(d))}function d(a){var b,c;try{c=E(a).result}catch(n){c=void 0}c||(b=z("%s: %s","UnknownError","An unknown error ocurred"));e(b)}function c(a){var b,c;try{c=E(a).response}catch(n){c=
void 0}if(!c||c.error)a="UnknownError",b="An unknown error ocurred",c&&c.error&&c.error.code&&c.error.message&&(a=c.error.code,b=c.error.message),b=z("%s: %s",a,b);e(b)}function e(a){a&&A("logout",a)}w.ba=function(){var c=q.f.getItem(w.g),d=v.H();c&&q.f.removeItem(w.g);!c&&d&&(c=d.access_token);v.w();c&&a(c);M()&&b()}})();var Na=["connectedAuth_general"],Oa="profile postal_code payments:widget payments:shipping_address payments:billing_address payments:partial_billing_address payments:autopay_consent".split(" ");
function La(b,a){var d=Pa();return null!==d&&d in b?a?b.lwa_general:b[d]:"/ap/oa"}function M(){if(w.aa())return!1;var b=Pa();if(null!==b)return-1!==Na.indexOf(b)}function Ma(b,a,d,c){a&&(a=Qa(d)!==Qa(c));return a||!Ra(b)?("undefined"!==typeof window.OffAmazonPayments&&"undefined"!==typeof window.OffAmazonPayments.Widgets&&"undefined"!==typeof window.OffAmazonPayments.Widgets.Utilities&&window.OffAmazonPayments.Widgets.Utilities.createCookie("amazon-pay-connectedAuth","lwa_general",0),!1):M()}
function Qa(b){var a=document.createElement("a");a.href=b;return a.hostname}function Ra(b){var a=!0;return b?(b.c(function(b){-1===Oa.indexOf(b)&&(a=!1)}),a):!1}function Pa(){if(document.cookie&&""!==document.cookie)for(var b=document.cookie.split(";"),a=0;a<b.length;a++){var d=b[a].split("\x3d");if(!d[0].replace(/ /,"").indexOf("amazon-pay-connectedAuth"))return d[1]}return null}window.amazon=window.amazon||{};window.amazon.Login=window.amazon.Login||{};window.amazon.Login.getClientId=function(){return w.I()};
window.amazon.Login.setClientId=function(b){return w.da(b)};window.amazon.Login.setMerchantID=function(b){return w.ga(b)};window.amazon.Login.setDomain=function(b){return w.o(b)};window.amazon.Login.setLWADomain=function(b){return w.O(b)};window.amazon.Login.setAPIDomain=function(b){return w.C(b)};window.amazon.Login.setSandboxMode=function(b){return w.ia(b)};window.amazon.Login.setSiteDomain=function(b){return q.o(b)};window.amazon.Login.Region=w.U;window.amazon.Login.Metrics=w.u;
window.amazon.Login.setRegion=function(b){return w.ha(b)};window.amazon.Login.setWebflowParams=function(b,a,d){return w.P(b,a,d)};window.amazon.Login.setLanguage=function(b){return w.ea(b)};window.amazon.Login.setLanguageHint=function(b){return w.fa(b)};window.amazon.Login.setUseCookie=function(b){return w.ja(b)};window.amazon.Login.authorize=function(b,a){return w.F(b,a)};window.amazon.Login.logout=function(){return w.ba()};window.amazon.Login.retrieveProfile=function(b,a){return x.N(b,a)};
"undefined"!==typeof window.OffAmazonPayments&&"undefined"!==typeof window.OffAmazonPayments.Config&&w.P(window.OffAmazonPayments.Config.COE,window.OffAmazonPayments.Config.LEDGER_CURRENCY,window.OffAmazonPayments.Config.ENV);"undefined"!==typeof window.OffAmazonPayments&&"undefined"!==typeof window.OffAmazonPayments.Widgets&&"undefined"!==typeof window.OffAmazonPayments.Widgets.Utilities&&window.OffAmazonPayments.Widgets.Utilities.setLoginDomain("");if("function"==typeof window.onAmazonLoginReady)window.onAmazonLoginReady();
M()&&v.W();
})();
}
