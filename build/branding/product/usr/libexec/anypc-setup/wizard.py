"""AnyPC's graphical front end for the offline installer."""

import os
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk, Pango

import backend
from controller import Controller


WORDMARK = "/usr/share/anaconda/pixmaps/anypc/wordmark.svg"
MIB = 1024 ** 2
GIB = 1024 ** 3
STEPS = ("welcome", "storage", "profile", "review", "install")
LABELS = {
    "welcome": ("Start", "Început"),
    "storage": ("Storage", "Stocare"),
    "profile": ("Profile", "Profil"),
    "review": ("Review", "Verificare"),
    "install": ("Installation", "Instalare"),
    "continue": ("Continue", "Continuă"),
    "back": ("Back", "Înapoi"),
    "start_title": ("Install AnyPC OS", "Instalează AnyPC OS"),
    "start_intro": (
        "Choose your language, then set up the drive and profile for this computer.",
        "Alege limba, apoi configurează discul și profilul pentru acest calculator.",
    ),
    "language": ("Installation language", "Limba instalării"),
    "disk_title": ("Choose a destination", "Alege discul de instalare"),
    "disk_intro": (
        "Select the drive where AnyPC OS will be installed.",
        "Selectează discul pe care vrei să instalezi AnyPC OS.",
    ),
    "choose_disk": ("Select a drive", "Selectează un disc"),
    "reload": ("Refresh drives", "Caută din nou"),
    "scan_error": ("The drive list could not be read.", "Lista de discuri nu a putut fi citită."),
    "no_disks": ("No eligible drive found.", "Nu am găsit niciun disc disponibil."),
    "layout": ("Partition layout", "Partiționare"),
    "auto": ("Automatic", "Automată"),
    "custom": ("Custom sizes", "Dimensiuni personalizate"),
    "boot": ("Boot partition (MiB)", "Partiția de pornire (MiB)"),
    "swap": ("Swap partition (MiB, 0 to skip)", "Partiția swap (MiB, 0 pentru a omite)"),
    "remaining": ("The system partition uses the remaining space.", "Partiția de sistem folosește spațiul rămas."),
    "profile_title": ("Create your AnyPC profile", "Creează profilul AnyPC"),
    "profile_intro": ("Your name appears in the console.", "Acest nume apare în consolă."),
    "profile_name": ("Display name", "Nume de profil"),
    "timezone": ("Time zone", "Fus orar"),
    "keyboard": ("Keyboard layout", "Dispunerea tastaturii"),
    "review_title": ("Review the installation", "Verifică instalarea"),
    "review_intro": (
        "The selected drive will be erased when installation starts.",
        "Toate datele de pe discul ales vor fi șterse când începe instalarea.",
    ),
    "review_drive": ("Target drive", "Disc de destinație"),
    "review_auto": ("Create the required partitions automatically.", "Creează automat partițiile necesare."),
    "review_custom": (
        "Boot: {boot} MiB · Swap: {swap} MiB · System: remaining space",
        "Pornire: {boot} MiB · Swap: {swap} MiB · Sistem: spațiul rămas",
    ),
    "erase_check": (
        "I confirm that all data on {device} can be erased.",
        "Confirm că toate datele de pe {device} pot fi șterse.",
    ),
    "install_button": ("Install AnyPC OS", "Instalează AnyPC OS"),
    "work_title": ("Installing AnyPC OS", "Se instalează AnyPC OS"),
    "preparing": ("Checking the selected drive", "Verificăm discul selectat"),
    "partitioning": ("Preparing partitions", "Pregătim partițiile"),
    "installing": ("Copying the system", "Copiem sistemul"),
    "finishing": ("Finishing setup", "Finalizăm configurarea"),
    "failure_title": ("Installation stopped", "Instalarea s-a oprit"),
    "failure_intro": ("Review the details before trying again.", "Verifică detaliile înainte de a încerca din nou."),
    "complete_title": ("AnyPC OS is ready", "AnyPC OS este gata"),
    "complete_intro": (
        "Restart the computer and boot from the installed drive.",
        "Repornește calculatorul și alege discul pe care ai instalat sistemul.",
    ),
    "reboot": ("Restart", "Repornește"),
    "reboot_failure": ("The computer could not be restarted.", "Calculatorul nu a putut fi repornit."),
    "details": ("Technical details", "Detalii tehnice"),
    "validation_error": ("Check the highlighted settings and try again.", "Verifică setările și încearcă din nou."),
}


def initial_language():
    try:
        command_line = Path("/proc/cmdline").read_text().split()
    except OSError:
        command_line = []
    for option in command_line:
        if option.startswith("inst.lang="):
            return int(option.removeprefix("inst.lang=").startswith("ro"))
    return int(os.environ.get("LANG", "").startswith("ro"))


def label(text, style=None):
    item = Gtk.Label(label=text)
    item.set_xalign(0)
    item.set_line_wrap(True)
    item.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    item.set_max_width_chars(56)
    if style:
        item.get_style_context().add_class(style)
    return item


def card():
    container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    container.get_style_context().add_class("card")
    return container


class Wizard(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title="AnyPC Setup")
        self.set_default_size(1120, 720)
        self.connect("delete-event", lambda *_: True)
        self.language = initial_language()
        self.locale = ("en_US.UTF-8", "ro_RO.UTF-8")[self.language]
        self.disk = None
        self.layout = "automatic"
        self.boot_mib = 2048
        self.swap_mib = 0
        self.profile = ""
        self.timezone = ("UTC", "Europe/Bucharest")[self.language]
        self.keyboard = ("us", "ro")[self.language]
        self.install_error = None
        self.plan = None
        self.show_page("welcome")
        self.fullscreen()
        self.controller = Controller(self)

    def t(self, key):
        return LABELS[key][self.language]

    def show_page(self, page):
        self.page = page
        old = self.get_child()
        if old:
            self.remove(old)
        frame = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(frame)
        frame.pack_start(self.rail(), False, False, 0)

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main.get_style_context().add_class("workspace")
        frame.pack_start(main, True, True, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_shadow_type(Gtk.ShadowType.NONE)
        main.pack_start(scroll, True, True, 0)

        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.body.set_border_width(28)
        scroll.add(self.body)

        self.footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.footer.get_style_context().add_class("footer")
        main.pack_end(self.footer, False, False, 0)
        self.back_button = Gtk.Button(label=self.t("back"))
        self.action_button = Gtk.Button(label=self.t("continue"))
        self.action_button.get_style_context().add_class("primary")
        self.footer.pack_start(self.back_button, False, False, 0)
        self.footer.pack_end(self.action_button, False, False, 0)

        getattr(self, "_show_" + page)()
        self.show_all()
        self.back_button.set_visible(page in {"storage", "profile", "review"})
        self.action_button.set_visible(page != "install")

    def rail(self):
        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        rail.get_style_context().add_class("rail")
        rail.set_size_request(174, -1)
        image = Gtk.Image.new_from_file(WORDMARK)
        image.set_margin_bottom(16)
        rail.pack_start(image, False, False, 0)

        active = STEPS.index(self.page) if self.page in STEPS else len(STEPS) - 1
        for index, step in enumerate(STEPS):
            row = label(f"{index + 1:02d}   {self.t(step)}", "step")
            if index == active:
                row.get_style_context().add_class("current")
            elif index < active:
                row.get_style_context().add_class("visited")
            rail.pack_start(row, False, False, 0)
        return rail

    def heading(self, title, detail=None):
        self.body.pack_start(label(self.t(title), "title"), False, False, 0)
        if detail:
            self.body.pack_start(label(self.t(detail), "hint"), False, False, 0)

    def field(self, box, caption, widget):
        field = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        name = self.t(caption)
        field.pack_start(label(name, "caption"), False, False, 0)
        widget.get_accessible().set_name(name)
        field.pack_start(widget, False, False, 0)
        box.pack_start(field, box.get_orientation() == Gtk.Orientation.HORIZONTAL, True, 0)
        return widget

    def primary(self, handler, caption=None):
        if caption:
            self.action_button.set_label(self.t(caption))
        self.action_button.connect("clicked", handler)

    def go_back(self, page):
        self.back_button.connect("clicked", lambda *_: self.show_page(page))

    def _show_welcome(self):
        self.heading("start_title", "start_intro")
        panel = card()
        languages = Gtk.ComboBoxText()
        languages.append("en_US.UTF-8", "English")
        languages.append("ro_RO.UTF-8", "Română")
        languages.set_active(self.language)
        languages.connect("changed", self.language_changed)
        self.field(panel, "language", languages)
        self.body.pack_start(panel, False, False, 0)
        self.primary(lambda *_: self.show_page("storage"))

    def language_changed(self, combo):
        self.language = combo.get_active()
        self.locale = combo.get_active_id()
        self.timezone = ("UTC", "Europe/Bucharest")[self.language]
        self.keyboard = ("us", "ro")[self.language]
        self.show_page("welcome")

    def disk_summary(self, disk, serial=False):
        size = f"{disk.size / GIB:.1f}"
        if self.language:
            size = size.replace(".", ",")
        description = f"{disk.path} · {size} GiB"
        if disk.model:
            description = f"{disk.model} · {description}"
        if serial and disk.serial:
            description += f"\nS/N {disk.serial}"
        return description

    def _show_storage(self):
        self.heading("disk_title", "disk_intro")
        panel = card()
        self.disk_choice = Gtk.ComboBoxText()
        self.disk_choice.append("none", self.t("choose_disk"))
        try:
            self.disks = backend.discover_disks()
            if not self.disks:
                panel.pack_start(label(self.t("no_disks"), "hint"), False, False, 0)
        except (OSError, RuntimeError, ValueError):
            self.disks = []
            panel.pack_start(label(self.t("scan_error"), "notice"), False, False, 0)
        self.disk_choice.set_active(0)
        for index, disk in enumerate(self.disks):
            self.disk_choice.append(str(index), self.disk_summary(disk))
            if disk == self.disk:
                self.disk_choice.set_active(index + 1)
        picker = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        picker.pack_start(self.disk_choice, True, True, 0)
        refresh = Gtk.Button(label=self.t("reload"))
        refresh.connect("clicked", lambda *_: self.show_page("storage"))
        picker.pack_end(refresh, False, False, 0)
        panel.pack_start(picker, False, False, 0)
        self.body.pack_start(panel, False, False, 0)

        options = card()
        self.mode = Gtk.ComboBoxText()
        self.mode.append("automatic", self.t("auto"))
        self.mode.append("custom", self.t("custom"))
        self.mode.set_active_id(self.layout)
        self.field(options, "layout", self.mode)
        self.custom_fields = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.custom_fields.set_no_show_all(True)
        self.boot_size = Gtk.SpinButton.new_with_range(1024, 8192, 64)
        self.boot_size.set_value(self.boot_mib)
        self.swap_size = Gtk.SpinButton.new_with_range(0, 65536, 256)
        self.swap_size.set_value(self.swap_mib)
        self.field(self.custom_fields, "boot", self.boot_size)
        self.field(self.custom_fields, "swap", self.swap_size)
        self.custom_fields.pack_start(label(self.t("remaining"), "hint"), False, False, 0)
        options.pack_start(self.custom_fields, False, False, 0)
        self.body.pack_start(options, False, False, 0)

        self.mode.connect("changed", self.storage_changed)
        self.disk_choice.connect("changed", self.storage_changed)
        self.boot_size.connect("value-changed", self.storage_changed)
        self.swap_size.connect("value-changed", self.storage_changed)
        for child in self.custom_fields.get_children():
            child.show_all()
        self.storage_changed()
        self.go_back("welcome")
        self.primary(lambda *_: self.show_page("profile"))

    def storage_changed(self, *_):
        selected = self.disk_choice.get_active()
        self.disk = self.disks[selected - 1] if selected > 0 else None
        self.layout = self.mode.get_active_id()
        self.boot_mib = self.boot_size.get_value_as_int()
        self.swap_mib = self.swap_size.get_value_as_int()
        self.custom_fields.set_visible(self.layout == "custom")
        self.action_button.set_sensitive(self.disk is not None)

    def _show_profile(self):
        self.heading("profile_title", "profile_intro")
        panel = card()
        self.profile_field = Gtk.Entry(text=self.profile, max_length=16)
        self.field(panel, "profile_name", self.profile_field)
        self.body.pack_start(panel, False, False, 0)
        region = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12, homogeneous=True)
        self.timezone_field = Gtk.ComboBoxText()
        for timezone in ("UTC", "Europe/Bucharest"):
            self.timezone_field.append(timezone, timezone)
        self.timezone_field.set_active_id(self.timezone)
        self.keyboard_field = Gtk.ComboBoxText()
        self.keyboard_field.append("us", "English (US)")
        self.keyboard_field.append("ro", "Română")
        self.keyboard_field.set_active_id(self.keyboard)
        self.field(region, "timezone", self.timezone_field)
        self.field(region, "keyboard", self.keyboard_field)
        self.body.pack_start(region, False, False, 0)
        self.error_label = label("", "notice")
        self.body.pack_start(self.error_label, False, False, 0)
        self.details_box = Gtk.Expander(label=self.t("details"))
        self.details_box.set_no_show_all(True)
        self.details_label = label("")
        self.details_box.add(self.details_label)
        self.body.pack_start(self.details_box, False, False, 0)
        self.go_back("storage")
        self.primary(self.prepare_review)

    def prepare_review(self, *_):
        self.plan = None
        self.details_box.hide()
        self.profile = self.profile_field.get_text().strip()
        self.timezone = self.timezone_field.get_active_id()
        self.keyboard = self.keyboard_field.get_active_id()
        try:
            self.plan = backend.validate_plan(
                self.disk, self.layout, self.boot_mib, self.swap_mib,
                self.profile, self.locale, self.timezone, self.keyboard,
            )
        except (OSError, ValueError, RuntimeError) as error:
            self.error_label.set_text(self.t("validation_error"))
            self.details_label.set_text(str(error))
            self.details_label.show()
            self.details_box.show()
            return
        self.show_page("review")

    def _show_review(self):
        self.heading("review_title", "review_intro")
        summary = card()
        summary.pack_start(label(self.t("review_drive"), "caption"), False, False, 0)
        summary.pack_start(label(self.disk_summary(self.disk, serial=True)), False, False, 0)
        summary.pack_start(label(self.t("layout"), "caption"), False, False, 0)
        layout = self.t("review_auto") if self.layout == "automatic" else self.t("review_custom").format(
            boot=self.boot_mib, swap=self.swap_mib,
        )
        summary.pack_start(label(layout), False, False, 0)
        summary.pack_start(label(self.t("profile"), "caption"), False, False, 0)
        summary.pack_start(label(f"{self.profile} · {self.timezone}"), False, False, 0)
        self.body.pack_start(summary, False, False, 0)
        self.erase = Gtk.CheckButton()
        self.erase.get_style_context().add_class("erase")
        agreement = self.t("erase_check").format(device=self.disk.path)
        self.erase.add(label(agreement))
        self.erase.get_accessible().set_name(agreement)
        self.body.pack_start(self.erase, False, False, 0)
        self.action_button.set_sensitive(False)
        self.erase.connect("toggled", lambda button: self.action_button.set_sensitive(button.get_active()))
        self.go_back("profile")
        self.primary(self.begin_install, "install_button")

    def begin_install(self, *_):
        if self.page != "review" or not self.erase.get_active() or self.plan is None:
            return
        plan = self.plan
        self.plan = None
        self.show_page("install")
        threading.Thread(target=self.install_worker, args=(plan,), daemon=True).start()

    def _show_install(self):
        self.heading("work_title")
        panel = card()
        self.current_phase = label(self.t("preparing"), "caption")
        panel.pack_start(self.current_phase, False, False, 0)
        self.progress = Gtk.ProgressBar()
        panel.pack_start(self.progress, False, False, 0)
        self.body.pack_start(panel, False, False, 0)
        GLib.timeout_add(115, self.pulse)

    def pulse(self):
        if self.page != "install":
            return GLib.SOURCE_REMOVE
        self.progress.pulse()
        return GLib.SOURCE_CONTINUE

    def show_phase(self, phase):
        if self.page == "install" and phase in {"preparing", "partitioning", "installing", "finishing"}:
            self.current_phase.set_text(self.t(phase))
        return GLib.SOURCE_REMOVE

    def install_worker(self, plan):
        try:
            backend.run_install(plan, lambda phase: GLib.idle_add(self.show_phase, phase))
        except Exception as error:
            GLib.idle_add(self.finish_install, str(error))
        else:
            GLib.idle_add(self.finish_install, None)

    def finish_install(self, error):
        self.install_error = error
        self.show_page("failure" if error is not None else "done")
        return GLib.SOURCE_REMOVE

    def _show_failure(self):
        self.heading("failure_title", "failure_intro")
        details = Gtk.Expander(label=self.t("details"))
        details.add(label(self.install_error, "notice"))
        self.body.pack_start(details, False, False, 0)
        self.primary(self.request_reboot, "reboot")

    def _show_done(self):
        self.heading("complete_title", "complete_intro")
        self.primary(self.request_reboot, "reboot")

    def request_reboot(self, *_):
        self.action_button.set_sensitive(False)
        try:
            backend.reboot()
        except (OSError, RuntimeError):
            self.body.pack_start(label(self.t("reboot_failure"), "notice"), False, False, 0)
            self.action_button.set_sensitive(True)
            self.body.show_all()


class SetupApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="ro.anypc.Setup")

    def do_activate(self):
        window = self.get_active_window()
        if window:
            window.present()
            return
        provider = Gtk.CssProvider()
        provider.load_from_path(str(Path(__file__).with_name("wizard.css")))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        Wizard(self).present()


if __name__ == "__main__":
    raise SystemExit(SetupApplication().run())
