export type Waypoint={x:number;y:number;wait:number};
export type Mission={id:string;name:string;speed:number;state:string;waypoints:Waypoint[]};
export type Telemetry={id:string;name:string;source:string;timestamp:number;connected:boolean;mode:string;state:string;latched:boolean;reason:string;position:{x:number;y:number;heading:number;speed:number;angular:number;distance:number};sensors:Record<string,Record<string,number|string|boolean|null>>;faults:Record<string,boolean>;settings:Record<string,number>;mission:{id:string|null;name:string;state:string;index:number;count:number;waypoints:Waypoint[]};trail:number[][]};
export type User={username:string;role:'ADMIN'|'OPERATOR'|'VIEWER'};
