// wom_base.js
// Copyright (C) 2015-2019 Thibauld Nion
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


function $(...args)
{
    return document.querySelector(...args);
}

// Get a cookie
// (adapted from https://docs.djangoproject.com/en/dev/ref/contrib/csrf/)
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
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

function countVisible(selector)
{
  let allMatches = document.querySelectorAll(selector);
  var count = 0;
  for (var i = 0; i < allMatches.length; i++)
  {
    let currentElement = allMatches[i];
    let computedStyle = window.getComputedStyle(currentElement);
    let isHidden = ((computedStyle.display === 'none') || (computedStyle.visibility === 'hidden'))
    if (isHidden)
      count++;
  }
  return count;
}

function updateNotificationMenuVisibility() {
  let numActiveNotifications = countVisible("#notifications .dropdown-item");
  let notificationDropdownElt = document.querySelector("#notifications");
  if (numActiveNotifications > 0)
    notificationDropdownElt.style.display = "block";
  else
    notificationDropdownElt.style.display = "none";
}

function notificationsOpened() {
  let notificationIconElt = document.querySelector("#notifications-icon");
  notificationIconElt.classList.remove("bi-bell-fill");
  notificationIconElt.classList.add("bi-bell");
}

// Show one of the warning that are written but hidden by default on
// the page, and that are identified via their HTML id.
// WARNING: if there are several warnings, they may overlap (TODO: in
// such case use a warning counter + a shift computed accordingly)
function showWarning(warningId) {
  let warningElt = document.querySelector("#"+warningId);
  if (warningElt)
  {
    warningElt.style.display = "block";
    let notificationIconElt = document.querySelector("#notifications-icon");
    notificationIconElt.classList.remove("bi-bell");
    notificationIconElt.classList.add("bi-bell-fill");
  }
  updateNotificationMenuVisibility();
}

// Hide a specific warning.
function hideWarning(warningId) {
  let warningElt = document.querySelector("#"+warningId);
  if (warningElt)
  {
    warningElt.style.display = "none";
  }
  updateNotificationMenuVisibility();
}


// Perform a REST request to one of wom's resources
function womRequest(verb, url, dataType, data)
{
  var csrftoken = getCookie('csrftoken');
  const headers = new Headers();
  headers.append("Content-Type", dataType);
  if (!csrfSafeMethod(verb)) {
      headers.append("X-CSRFToken", csrftoken);
  }
  return fetch(url, {
    mode: "same-origin", // obviates need for sameOrigin test
    method: verb,
    body: data,
    headers: headers
  });
}


// Request the sieve to drop its content
function dropSieveContent(sieveURL)
{
  womRequest("POST", sieveURL,
             "application/json", JSON.stringify({"action": "drop"}))
    .then(function () {window.location.href = sieveURL})
    .catch(function () {showWarning("wom-drop-sieve-content-failed")});
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
  if ($("#edit-toggle").classList.contains("edit-on"))
  {
      $(".read-only").classList.remove("edit-on");
      $(".edit-only").classList.remove("edit-on");
      $("#edit-toggle").classList.remove("edit-on");
  }
  else
  {
      $(".read-only").classList.add("edit-on");
      $(".edit-only").classList.add("edit-on");
      $("#edit-toggle").classList.add("edit-on");
  }
}
