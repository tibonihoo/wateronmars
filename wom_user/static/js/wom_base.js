// wom_base.js
// Copyright 2015 Thibauld Nion
//
// This file is part of WaterOnMars (https://github.com/tibonihoo/wateronmars).
//
// WaterOnMars is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// WaterOnMars is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with WaterOnMars.  If not, see <http://www.gnu.org/licenses/>.
//
//
// Requirements:
// - jquery v1.8.2


// using jQuery to get a cookie 
// (from https://docs.djangoproject.com/en/dev/ref/contrib/csrf/)
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Django-specific method to distinguish which request needs to take
// care of the crsf protection
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// Show one of the warning that are written but hidden by default on
// the page, and that are identified via their HTML id.
// WARNING: if there are several warnings, they may overlap (TODO: in
// such case use a warning counter + a shift computed accordingly)
function showWarning(warningId) {
  var warningElt = $("#"+warningId);
  warningElt.popover();
  warningElt.css({ 
    "display": "block",
  });
}

// Hide a specific warning.
function hideWarning(warningId) {
  $("#"+warningId).css("display", "none");
}


// Perform a REST request to one of wom's resources
function womRequest(verb, url, dataType, data)
{
  var csrftoken = getCookie('csrftoken');
  return $.ajax({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
      if (!csrfSafeMethod(settings.type)) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
    },
    type: verb,
    url: url,
    data: data,
    dataType: dataType,
  })
}


// Request the sieve to drop its content
function dropSieveContent(sieveURL)
{
  womRequest("POST", sieveURL,
             "json", JSON.stringify({"action": "drop"}))
    .done(function () {window.location.href = sieveURL})
    .fail(function () {showWarning("wom-drop-sieve-content-failed")});
}

// For pages that have an "edit-mode"
// Assumes:
// 1/ that the page has a "toggle" element with id="edit-toggle"
// 2/ that items that must be acivated only in edit mode have the
// "edit-tool" class
// 3/ that the css properties for these id and class are correct (as
// provided by wom_base.css)
function toggleEditMode()
{
  if ($("#edit-toggle").hasClass("edit-on"))
  {
      $(".edit-tool").removeClass("edit-on")
      $("#edit-toggle").removeClass("edit-on")
  }
  else
  {
    $(".edit-tool").addClass("edit-on")
    $("#edit-toggle").addClass("edit-on")
  }
}
