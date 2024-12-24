init -990 python:
    store.mas_submod_utils.Submod(
        author="Friends of Monika",
        name="Log Screen",
        description=_("Display all MAS logs right in game in a configurable log screen."),
        version="1.0.3",
        settings_pane="fom_log_screen_config"
    )

init -989 python:
    if store.mas_submod_utils.isSubmodInstalled("Submod Updater Plugin"):
        store.sup_utils.SubmodUpdater(
            submod="Log Screen",
            user_name="friends-of-monika",
            repository_name="mas-logscreen",
            extraction_depth=2
        )
