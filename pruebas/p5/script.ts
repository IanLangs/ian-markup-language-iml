class python {
    name: string;
    version: number;
    int: Function;
    print: Function;
    constructor(version:number) {
        this.version = version;
        this.name = "python"
        this.int = function(x:string) {return parseInt(x)}
        this.print = console.log
    }
    
    type(object: any): unknown {
        return typeof(object)
    }
    lambda(args: any[], code:string): Function {
        return new Function(...args, code)
    }
    round(x: number) {
        if ((x - Math.floor(x)) == 0.5) {
            if (parity(Math.floor(x))) {
                return Math.floor(x)
            } else {
                return Math.ceil(x)
            }
        }else {return Math.round(x)}
    }
    pymod(a:number, b:number) {return ((a % b) + b) % b}
}
const py314 = new python(3.14); export {py314}
function parity(n:number) {return py314.pymod(n, 2) == 0}
function hola(name: String="placeholder"): void {console.log("hola " + name)}export {hola}
console.log(py314.int("8.9"))
