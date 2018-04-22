################################################################################
# Project: LimeBud
# Version: 1.0.0 (2018-04-22)
# License: ISC
#
# Developer(s):
# - Martin Weigel <mail@MartinWeigel.com>
################################################################################
import sublime, sublime_plugin, re
from collections import defaultdict

class LimebudCommand(sublime_plugin.TextCommand):
    _inverse_budget = False
    _percentages_only = False

    STYLE = """ <style>
                    #limebud_report {
                        margin-top: 1rem;
                        padding: 0.5rem;
                        width: 71rem;
                        border-top: 5px solid color(var(--foreground));
                        background-color: #333;
                    }
                    .budget_positive {
                        display: inline;
                        color: #00FF00;
                        border-right: 3px solid color(var(--foreground));
                    }
                    .budget_negative {
                        display: inline;
                        color: #FF0000;
                        border-right: 3px solid color(var(--foreground));
                    }
                    .chart_in {
                        background-color: color(var(--foreground));
                        display: inline;
                    }
                    .chart_out {
                        display: inline;
                        border-right: 3px solid color(var(--foreground));
                    }
                    .border_right { border-right: 3px solid color(var(--foreground)); }
                    .chart_positive { background-color: #00FF00; }
                    .chart_negative { background-color: #FF0000; }
                    .char_line { height: 0.5rem; }
                </style> """

    def run(self, view):
        self.view.erase_phantoms("report")
        self.load_settings()

        # Dictionary to sum up the expenses per category
        buckets = defaultdict(lambda: 0.0, {})

        # Get content of file from sublime
        document_region = sublime.Region(0, self.view.size())
        contents = self.view.substr(document_region)
        lines = contents.splitlines()
        line_regions = self.view.split_by_newlines(document_region)   

        # Iterate over all lines to calculate total
        for index, line in enumerate(lines):
            cols = re.split(r'\s+', line)
            if(len(cols) >= 3):
                try:
                    value = float(cols[2])
                    buckets[cols[1]] += value
                except Exception as e:
                    self.mark_error(line_regions, index, line)
                
        # Create output in sublime
        report = self.generate_report(buckets)
        if report:
            self.view.add_phantom("report", line_regions[-1], report, sublime.LAYOUT_BLOCK)


    def load_settings(self):
        settings = self.view.settings()
        self._inverse_budget = settings.get("limebud.invert", False)
        self._percentages_only = settings.get("limebud.percentages_only", False)


    def generate_report(self, buckets):
        report = '<html><body id="limebud_report">'
        report += self.STYLE

        if len(buckets) > 0:
            positives = sum(v for v in buckets.values() if v > 0)
            negatives = sum(v for v in buckets.values() if v < 0)

            if(self._inverse_budget):
                positives, negatives = -negatives, -positives

            for category, expense in sorted(buckets.items()):
                if(self._inverse_budget):
                    expense = -expense
                percentage = 100*expense / positives if expense > 0 else 100*expense / negatives
                report += self.print_entry_line(category, expense, percentage)

            report += '<div class="char_line"></div>'
            report += self.print_entry_line('TOTAL', positives+negatives, -100*negatives/positives if positives > 0 else 100)
            return report + '</body></html>'
        else:
            sublime.error_message('No entries found. Could not calculate a budget report')

    # Creates string for one entry bucket
    def print_entry_line(self, text, expense, percentage):
        category_class = 'budget_positive' if expense >= 0 else 'budget_negative'
        category_text = '{0:15} {1:>10.2f} '.format(text, expense).replace(' ', '&nbsp;')
        report = '<p class="{0}">{1}</p>'.format(category_class, category_text)

        if not self._percentages_only:
            classes = 'chart_positive' if expense > 0 else 'chart_negative'
            classes += ' border_right' if percentage >= 100 else ''
            report += self.print_chart(percentage, classes)
        else:
            report += ' {0:>4.2f}'.format(percentage).replace(' ', '&nbsp;')

        report += '<br>'
        return report;

    # Creates HTML barchart using divs
    def print_chart(self, percentage, classes='', inside_char = '&nbsp;', outside_char = '&nbsp;'):
        percentage = min(max(percentage, 0), 100)
        inside_spacing  = inside_char  * int(round(abs(percentage)))
        outside_spacing = outside_char * int(round(100-abs(percentage)))
        inside  = '<div class="chart_in {1}">{0}</div>'.format(inside_spacing, classes)
        outside = '<div class="chart_out">{0}</div>'.format(outside_spacing)
        return inside + outside

    # Prints a dot next to the line number
    def mark_error(self, line_regions, index, line):
        self.view.add_regions(str(index), [line_regions[index]], "red", "dot",
            sublime.HIDDEN | sublime.PERSISTENT)
