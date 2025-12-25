// **=======================================**
// ||          <<<<< OPTIONS >>>>>          ||
// **=======================================**

#let ticket_type_max_font_size = 41pt
#let ticket_type_min_font_size = 26.6pt

#let title_max_font_size = 27pt
#let title_min_font_size = 22pt

#let sub_title_max_font_size = 21pt
#let sub_title_min_font_size = 17pt


// **========================================**
// ||          <<<<< CLI ARGS >>>>>          ||
// **========================================**

#let ticket_type = sys.inputs.at("ticket_type", default: "Ticket")
#let title = sys.inputs.at("title", default: none)
#let sub_title = sys.inputs.at("sub_title", default: none)
#let due_date_str = sys.inputs.at("due_date_str", default: none)
#let due_time_str = sys.inputs.at("due_time_str", default: none)
#let extra_content = sys.inputs.at("extra_content", default: none)
#let ticket_revision = int(sys.inputs.at("revision", default: 1))


// **==========================================**
// ||          <<<<< PAGE SETUP >>>>>          ||
// **==========================================**

#set page(width: 78mm, height: auto, margin: (bottom: 2mm, rest: 1mm))
#set text(size: 13pt)

#set rect(radius: 5pt, stroke: (
  thickness: 3pt,
))


// **=========================================**
// ||          <<<<< FUNCTIONS >>>>>          ||
// **=========================================**

#let parseDatetime(date_str, time_str) = {
  // Set up a dictionary for holding the parameters for the date-time.
  let dt_params = (:)

  // Parse values from the date and time strings.
  let (year, month, day) = if (type(date_str) == str) {
    date_str.split("-").map(e => int(e))
  } else { (none,) * 3 }
  let (hour, minute, second, ..) = (
    (
      if (type(time_str) == str) {
        time_str.split(":").map(e => int(e))
      } else { () }
    )
      + (none,) * 3
  )

  let noneFallback(val, default) = if (val != none) { val } else { default }

  // Construct the date-time with default values.
  let dt = datetime(
    year: noneFallback(year, 1970),
    month: noneFallback(month, 1),
    day: noneFallback(day, 1),
    hour: noneFallback(hour, 0),
    minute: noneFallback(minute, 0),
    second: noneFallback(second, 0),
  )

  return dt
}

#let elementFontScaler(min_font_size, max_font_size, elem_func) = {
  return (
    context [
      // Decrease the font size until it fits (or reaches the minimum font
      // size).
      #layout(size => {
        let _font_size = max_font_size

        // let ticket_type_element = ticket_type_element_constructor(font_size)
        let elem = elem_func(_font_size)
        while (
          _font_size >= min_font_size and measure(elem).width > size.width
        ) {
          _font_size = _font_size - 0.1pt
          elem = elem_func(_font_size)
        }

        [#elem]
      })
    ]
  )
}

#let ticketTemplate(
  ticket_type,
  title: none,
  sub_title: none,
  due_date_str: none,
  due_time_str: none,
  ticket_revision: 0,
  content: none,
) = {
  let due_dt = parseDatetime(due_date_str, due_time_str)

  let due_grid_params = ()

  if (due_date_str != none) {
    due_grid_params.push(text([Due Date:]))
    due_grid_params.push(text(
      due_dt.display("[month repr:short] [day], [year]"),
      weight: 700,
      size: 20pt,
    ))
  }
  if (due_time_str != none) {
    due_grid_params.push([Due Time:])
    due_grid_params.push(text(
      due_dt.display("[hour repr:24 padding:zero]:[minute padding:zero]"),
      weight: 700,
      size: 20pt,
    ))
  }

  return [
    #rect(
      width: 100%,
      inset: (top: 4mm, bottom: 2.2mm),
      [
        #set align(center)

        #stack(
          dir: ttb,

          // ----- TICKET TYPE -----
          elementFontScaler(
            ticket_type_min_font_size,
            ticket_type_max_font_size,
            font_size => box(
              inset: (x: 6pt),
              rect(
                text(size: font_size, weight: 900, upper(ticket_type.trim())),
                inset: 2.5mm,
              ),
            ),
          ),

          // ----- TITLE -----
          v(15pt),
          elementFontScaler(
            title_min_font_size,
            title_max_font_size,
            font_size => text(
              underline(smallcaps(title), stroke: (cap: "round")),
              size: font_size,
              weight: 600,
            ),
          ),

          // ----- SUB-TITLE -----
          v(13pt),
          elementFontScaler(
            sub_title_min_font_size,
            sub_title_max_font_size,
            font_size => text(
              smallcaps(sub_title),
              size: font_size,
              weight: 600,
              style: "italic",
            ),
          ),

          // ----- DUE DATE -----
          ..if (due_date_str != none or due_time_str != none) {
            (
              v(14pt),
              line(length: 20%, stroke: (cap: "round")),
              box(
                inset: (top: 12pt, bottom: 11pt - 1mm),
                {
                  show grid: set text(size: 14pt)
                  grid(
                    columns: 2,
                    align: (right + horizon, left + horizon),
                    column-gutter: 0.4em,
                    row-gutter: 0.5em,

                    ..due_grid_params
                  )
                },
              ),
            )
          },

          // Render any extra content.
          if (content != none) [
            #v(1.5mm)
            #line(length: 98%, stroke: (cap: "round", thickness: 1.2pt))
            #v(-9pt)
            #set align(left)
            #content
          ],
        )

      ],
    )

    #if (ticket_revision > 1) {
      place(top + right, dx: 1.5mm, dy: -1.5mm, rotate(
        30deg,
        reflow: true,
        box(
          fill: black.transparentize(44%),
          radius: 5pt,
          inset: 3pt,
          stroke: white + 1.5pt,
          text(
            size: 22pt,
            fill: white,
            [Revision #ticket_revision],
          ),
        ),
      ))
    }
  ]
}


// **====================================**
// ||          <<<<< MAIN >>>>>          ||
// **====================================**

#ticketTemplate(
  ticket_type,
  title: title,
  sub_title: sub_title,
  due_date_str: due_date_str,
  due_time_str: due_time_str,
  content: extra_content,
  ticket_revision: ticket_revision,
)

