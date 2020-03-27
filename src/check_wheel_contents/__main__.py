from   pathlib   import Path
from   typing    import Iterable, List, Optional, Set
import click
from   .         import __version__
from   .checker  import WheelChecker
from   .checks   import Check, parse_checks_string
from   .contents import WheelContents
from   .errors   import UserInputError

class ChecksParamType(click.ParamType):
    name = 'checks'

    def convert(
        self,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Set[Check]:
        try:
            return parse_checks_string(value)
        except UserInputError as e:
            self.fail(str(e), param, ctx)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(
    __version__,
    '-V', '--version',
    message = '%(prog)s %(version)s',
)
@click.option(
    '-c', '--config',
    type = click.Path(exists=True, dir_okay=False),
    help = 'Use the specified configuration file',
)
@click.option(
    '--ignore',
    type    = ChecksParamType(),
    help    = 'Comma-separated list of checks to disable',
    metavar = 'CHECKS',
)
@click.option(
    '--select',
    type    = ChecksParamType(),
    help    = 'Comma-separated list of checks to enable',
    metavar = 'CHECKS',
)
@click.argument('wheel', nargs=-1, type=click.Path(exists=True, dir_okay=True))
@click.pass_context
def main(
    ctx: click.Context,
    wheel: List[str],
    config: Optional[str],
    select: Optional[Set[Check]],
    ignore: Optional[Set[Check]],
) -> None:
    checker = WheelChecker()
    try:
        checker.read_config_file(config)
        checker.load_command_options(select=select, ignore=ignore)
        checker.finalize_options()
    except UserInputError as e:
        ctx.fail(str(e))
    ok = True
    for w in args2wheelpaths(wheel):
        contents = WheelContents.from_wheel(w)
        failures = checker.check_contents(contents)
        if failures:
            for f in failures:
                print(f.show(str(w)))
            ok = False
        else:
            print(f'{w}: OK')
    ctx.exit(0 if ok else 1)

def args2wheelpaths(args: List[str]) -> Iterable[Path]:
    for a in args:
        p = Path(a)
        if p.is_dir():
            yield from p.glob('**/*.whl')
        else:
            yield p

if __name__ == '__main__':
    main()
