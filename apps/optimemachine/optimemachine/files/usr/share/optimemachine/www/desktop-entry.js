const frames = new WeakMap();
export async function bootstrap() {}
export async function mount({domElement}) {
 const frame=document.createElement('iframe');frame.src='/apps/optimemachine/';frame.title='时光机';frame.style.cssText='border:0;width:100%;height:100%;display:block';domElement.append(frame);frames.set(domElement,frame);
}
export async function unmount({domElement}) {frames.get(domElement)?.remove();frames.delete(domElement);}
